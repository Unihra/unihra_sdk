"""
Unihra MCP Server
=================
File-backed MCP server for the Unihra SEO & Semantic Analysis SDK.

Architecture
------------
1. unihra_analyze  — runs the full analysis, saves the raw result to a local
   JSON file, returns only a result_id + a compact summary to the model.
   The model never receives the full payload (which can be 200k+ chars).

2. unihra_get_*    — each tool loads the saved file by result_id and returns
   only the requested slice, with light noise-filtering applied.
   The model iterates over slices as needed — no context overflow.

This means:
  • Nothing is lost  — the full result is always on disk.
  • Context stays small — the model sees summaries and targeted slices.
  • No hard limits on data richness — filters are soft and adjustable.

Storage
-------
Results are stored in UNIHRA_RESULTS_DIR (default: ~/.unihra_mcp/results/).
Each file is named {result_id}.json and kept indefinitely.
Call unihra_list_results / unihra_delete_result to manage them.

Run
---
    UNIHRA_API_KEY=your_key python -m unihra.mcp_server
    python -m unihra.mcp_server --key YOUR_KEY [--retries 3] [--results-dir /tmp/unihra]

Claude Desktop config
---------------------
{
  "mcpServers": {
    "unihra": {
      "command": "python",
      "args": ["-m", "unihra.mcp_server"],
      "env": {
        "UNIHRA_API_KEY": "YOUR_KEY_HERE",
        "UNIHRA_RESULTS_DIR": "/tmp/unihra_results"
      }
    }
  }
}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types as mcp_types
except ImportError:
    print(
        "ERROR: 'mcp' package not found.\n"
        "Install: pip install mcp\n"
        "Or:      pip install unihra[mcp]",
        file=sys.stderr,
    )
    sys.exit(1)

from .client import UnihraClient
from .exceptions import UnihraError

_JUNK_FIELDS: Set[str] = {
    "id", "block_id", "analysis_id",
    "created_at", "updated_at", "modified_at",
}

_ACTION_MAP: Dict[str, str] = {
    "Добавить":         "add",
    "Увеличить":        "increase",
    "Уменьшить":        "decrease",
    "Ок":               "ok",
    "Ничего не делать": "ok",
}

def _results_dir() -> Path:
    d = Path(os.environ.get("UNIHRA_RESULTS_DIR", Path.home() / ".unihra_mcp" / "results"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _save_result(result: dict, own_page: str, competitors: List[str]) -> str:
    """Save full raw result to disk, return result_id."""
    result_id = uuid.uuid4().hex[:12]
    payload = {
        "result_id":   result_id,
        "saved_at":    datetime.utcnow().isoformat(),
        "own_page":    own_page,
        "competitors": competitors,
        "data":        result,
    }
    path = _results_dir() / f"{result_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return result_id


def _load_result(result_id: str) -> dict:
    """Load a saved result. Raises ValueError if not found."""
    path = _results_dir() / f"{result_id}.json"
    if not path.exists():
        raise ValueError(
            f"Result '{result_id}' not found in {_results_dir()}. "
            "Run unihra_analyze first, or check unihra_list_results."
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["data"]


def _load_meta(result_id: str) -> dict:
    """Load metadata (without the heavy data payload)."""
    path = _results_dir() / f"{result_id}.json"
    if not path.exists():
        raise ValueError(f"Result '{result_id}' not found.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {k: v for k, v in payload.items() if k != "data"}

def _strip_junk(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_junk(v) for k, v in obj.items() if k not in _JUNK_FIELDS}
    if isinstance(obj, list):
        return[_strip_junk(i) for i in obj]
    return obj


def _norm_action(raw: str) -> str:
    return _ACTION_MAP.get(raw, raw).lower()

def _build_summary(result: dict, result_id: str, own_page: str, competitors: List[str]) -> dict:
    """
    Compact summary returned immediately after analysis.
    Model uses this to decide which unihra_get_* tools to call next.
    """
    gaps    = result.get("semantic_context_analysis") or result.get("semantic_context_gaps") or []
    blocks  = result.get("block_comparison") or[]
    ngrams  = result.get("ngrams_analysis") or result.get("n_grams_analysis") or[]
    drmaxs  = result.get("drmaxs") or {}
    struct  = result.get("page_structure") or[]
    anchors = result.get("anchors_analysis") or[]

    # Top-5 gaps by gap score
    top_gaps = sorted(gaps, key=lambda x: x.get("gap", 0), reverse=True)[:5]

    # Words needing action (not ok)
    action_counts: Dict[str, int] = {}
    for w in blocks:
        a = _norm_action(w.get("action_needed", "ok"))
        action_counts[a] = action_counts.get(a, 0) + 1

    # Top-5 n-grams by pages_count, missing from own page
    top_ngrams = sorted([n for n in ngrams if not n.get("present_on_own_page", True)],
        key=lambda x: x.get("pages_count", 0), reverse=True
    )[:5]

    # Top-5 missing anchors by competitor average frequency
    top_anchors = sorted([a for a in anchors if a.get("frequency_own", 0) == 0],
        key=lambda x: x.get("frequency_comp_avg", 0), reverse=True
    )[:5]

    # Own page structure snapshot
    own_struct = next((s for s in struct if s.get("url") == own_page), struct[0] if struct else {})
    own_snap = {
        "title":              (own_struct.get("meta_tags") or {}).get("title"),
        "h1":                 (own_struct.get("content") or {}).get("h1_heading"),
        "uniqueness_pct":     (own_struct.get("metrics") or {}).get("uniqueness_percentage"),
        "char_count":         (own_struct.get("metrics") or {}).get("char_count_no_spaces"),
        "heading_structure":  (own_struct.get("content") or {}).get("heading_structure_raw"),
    }

    return {
        "result_id":   result_id,
        "own_page":    own_page,
        "competitors": competitors,
        "data_blocks": {
            "page_structure":            len(struct),
            "semantic_context_analysis": len(gaps),
            "block_comparison":          len(blocks),
            "ngrams_analysis":           len(ngrams),
            "anchors_analysis":          len(anchors),
            "drmaxs_sections":           list(drmaxs.keys()),
        },
        "own_page_snapshot": own_snap,
        "top5_priority_gaps":[
            {
                "lemma":            g.get("lemma"),
                "gap":              g.get("gap"),
                "coverage_percent": g.get("coverage_percent"),
                "own_score":        g.get("own_score"),
                "recommendation":   g.get("recommendation"),
                "context_snippet":  g.get("context_snippet"),
            }
            for g in top_gaps
        ],
        "block_comparison_action_counts": action_counts,
        "top5_missing_ngrams":[
            {
                "ngram":         n.get("ngram"),
                "pages_count":   n.get("pages_count"),
                "frequency_avg": n.get("frequency_avg"),
            }
            for n in top_ngrams
        ],
        "top5_missing_anchors":[
            {
                "anchor":             a.get("anchor"),
                "frequency_comp_avg": a.get("frequency_comp_avg"),
                "pages_count":        a.get("pages_count"),
            }
            for a in top_anchors
        ],
        "next_steps": (
            "Use result_id with unihra_get_gaps, unihra_get_anchors, unihra_get_vectors, "
            "unihra_get_word_actions, unihra_get_ngrams, or unihra_get_page_structure "
            "to retrieve detailed data slices as needed."
        ),
    }

def build_server(client: UnihraClient) -> Server:
    server = Server("unihra-mcp")

    @server.list_tools()
    async def list_tools() -> list[mcp_types.Tool]:
        return[
            mcp_types.Tool(
                name="unihra_health",
                description="Check Unihra API availability. Returns service status.",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            mcp_types.Tool(
                name="unihra_analyze",
                description=(
                    "PRIMARY TOOL for SEO content analysis and page comparison.\n\n"
                    "USE THIS TOOL — not web fetching or manual parsing — whenever the user asks:\n"
                    "  • 'Compare page X with competitor Y'\n"
                    "  • 'Why does page X rank lower than Y?'\n"
                    "  • 'What content / words should I add to my page?'\n"
                    "  • 'What keywords do competitors use that I don't?'\n"
                    "  • 'Find semantic gaps / missing words on my page'\n"
                    "  • 'Do an SEO / content audit of URL X vs URL Y'\n"
                    "  • 'What should I write in Title / H1 / H2?'\n"
                    "  • 'Which LSI / semantic / vector words are missing from my page?'\n"
                    "  • Any task involving comparing text content of two or more URLs\n\n"
                    "DO NOT fetch or parse pages yourself — the tool handles everything server-side.\n\n"
                    "RESPONSE: Returns a result_id and a compact summary only.\n"
                    "The full result (~200k chars) is saved to disk automatically.\n"
                    "Use result_id with unihra_get_* tools to retrieve specific data slices.\n\n"
                    "Takes 30–120 seconds depending on page count and size."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "own_page": {
                            "type": "string",
                            "description": "URL of the page to optimise / audit.",
                        },
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Competitor page URLs. 3–10 recommended for statistical reliability.",
                        },
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Target search queries the page should rank for. "
                                "REQUIRED for zone recommendations (Add to Title/H1, Add to H2/H3 …). "
                                "Example: ['купить шланг', 'шланг высокого давления цена']"
                            ),
                        },
                        "lang": {
                            "type": "string",
                            "enum": ["ru", "en"],
                            "description": "Page language. Default: 'ru'.",
                        },
                        "url_cookies": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "description": (
                                "Per-URL cookies for pages behind auth / age gates. "
                                "Example: {\"https://example.com/page\": \"session=abc123\"}"
                            ),
                        },
                    },
                    "required":["own_page", "competitors"],
                },
            ),
            mcp_types.Tool(
                name="unihra_list_results",
                description=(
                    "List all saved analysis results on disk.\n"
                    "Returns result_id, own_page, competitors, and saved_at for each result.\n"
                    "Use to find a result_id for a previously analysed page."
                ),
                inputSchema={"type": "object", "properties": {}, "required":[]},
            ),
            mcp_types.Tool(
                name="unihra_delete_result",
                description="Delete a saved analysis result from disk by result_id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "ID of the result to delete."},
                    },
                    "required": ["result_id"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_page_structure",
                description=(
                    "Get page structure data from a saved analysis.\n\n"
                    "Returns for each URL (own page + competitors):\n"
                    "  • url, meta title, meta description\n"
                    "  • h1_heading, heading_structure_raw (H1–H6 tree as compact string)\n"
                    "  • uniqueness_percentage, char_count_no_spaces\n\n"
                    "Use to compare headings, titles, and content volume across pages."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "From unihra_analyze."},
                        "own_only": {
                            "type": "boolean",
                            "description": "Return only own page structure. Default false (all pages).",
                            "default": False,
                        },
                    },
                    "required": ["result_id"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_gaps",
                description=(
                    "Get semantic context gaps from a saved analysis.\n\n"
                    "Each gap item: lemma, gap score, coverage_percent (% of competitors using it), "
                    "own_score (0 = word absent or in weak zone), recommendation, context_snippet.\n\n"
                    "Results are sorted by gap desc (highest priority first).\n"
                    "Use to build a prioritised content brief: "
                    "which words to add to Title/H1, H2/H3, or body text."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "From unihra_analyze."},
                        "top_n": {
                            "type": "integer",
                            "description": "Max items to return. Default 50.",
                            "default": 50,
                        },
                        "min_coverage": {
                            "type": "number",
                            "description": (
                                "Min competitor coverage % to include. Default 20. "
                                "Lower to 10 when you have only 1–2 competitors."
                            ),
                            "default": 20.0,
                        },
                        "min_gap": {
                            "type": "number",
                            "description": "Min gap value. Default 0.5. Lower to 0 for full list.",
                            "default": 0.5,
                        },
                        "missing_only": {
                            "type": "boolean",
                            "description": "Only words absent from own page (own_score == 0). Default false.",
                            "default": False,
                        },
                        "group_by_recommendation": {
                            "type": "boolean",
                            "description": "Group results by recommendation type. Default false (flat list).",
                            "default": False,
                        },
                    },
                    "required": ["result_id"],
                },
            ),

            mcp_types.Tool(
                name="unihra_get_anchors",
                description=(
                    "Get anchor text (link texts) analysis from a saved analysis.\n\n"
                    "Each item: anchor, frequency_own, frequency_comp_avg, pages_count.\n\n"
                    "Use to find missing internal/external link texts that competitors use to rank."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "From unihra_analyze."},
                        "top_n": {
                            "type": "integer",
                            "description": "Max items to return. Default 50.",
                            "default": 50,
                        },
                        "missing_only": {
                            "type": "boolean",
                            "description": "Only anchors absent from own page (frequency_own == 0). Default false.",
                            "default": False,
                        },
                    },
                    "required": ["result_id"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_vectors",
                description=(
                    "Get Vector AI / LSI semantic words from a saved analysis.\n\n"
                    "DrMaxs uses neural embeddings to find words that are topically relevant "
                    "even if not used directly by competitors — latent semantic vocabulary.\n\n"
                    "Sections: by_tfidf (most unique signal), by_frequency, by_sites_count.\n"
                    "Sorted by similarity_score desc. Ranking is meaningful; "
                    "absolute score values are not (embedding scale varies by topic).\n\n"
                    "Use to expand content vocabulary beyond what competitors explicitly use."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "From unihra_analyze."},
                        "top_n": {
                            "type": "integer",
                            "description": "Max words per section. Default 40.",
                            "default": 40,
                        },
                        "missing_only": {
                            "type": "boolean",
                            "description": "Only words NOT on own page. Default true.",
                            "default": True,
                        },
                        "sections": {
                            "type": "array",
                            "items": {"type": "string", "enum":["by_tfidf", "by_frequency", "by_sites_count"]},
                            "description": "Which sections to return. Default:['by_tfidf', 'by_frequency'].",
                        },
                        "dedupe_with_gaps": {
                            "type": "boolean",
                            "description": (
                                "Exclude words already in semantic_context_analysis. "
                                "Default true — avoids showing the same word twice."
                            ),
                            "default": True,
                        },
                    },
                    "required": ["result_id"],
                },
            ),

            mcp_types.Tool(
                name="unihra_get_word_actions",
                description=(
                    "Get TF-IDF word comparison (block_comparison) from a saved analysis.\n\n"
                    "Each item: word, lemma, frequency, frequency_own_page, "
                    "pct_target (density on own page), pct_target_comp_avg (competitor avg density), "
                    "ratio_comp_avg, action_needed (add / increase / decrease / ok), "
                    "present_on_own_page.\n\n"
                    "Use to find over-optimised words (decrease) or underused ones (add/increase)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "From unihra_analyze."},
                        "action": {
                            "type": "string",
                            "enum":["add", "increase", "decrease", "ok", "all"],
                            "description": "Filter by action. Default 'all'.",
                            "default": "all",
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Max items per action group. Default 50.",
                            "default": 50,
                        },
                        "min_frequency": {
                            "type": "number",
                            "description": "Min word frequency. Default 1.0 (keep almost everything).",
                            "default": 1.0,
                        },
                        "exclude_ok": {
                            "type": "boolean",
                            "description": "Exclude ok-action words. Default true.",
                            "default": True,
                        },
                    },
                    "required": ["result_id"],
                },
            ),

            mcp_types.Tool(
                name="unihra_get_ngrams",
                description=(
                    "Get n-gram (phrase) analysis from a saved analysis.\n\n"
                    "Each item: ngram, ngram_type (bigrams / lemma_trigrams), "
                    "frequency_avg (avg occurrences per competitor page), "
                    "pages_count (how many competitor sites use this phrase), "
                    "present_on_own_page.\n\n"
                    "Note: present_on_own_page reflects exact phrase match on your page — "
                    "useful to verify which competitor patterns you already cover.\n\n"
                    "Use to find stable 2–3 word patterns to incorporate into content."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result_id": {"type": "string", "description": "From unihra_analyze."},
                        "top_n": {
                            "type": "integer",
                            "description": "Max phrases to return. Default 60.",
                            "default": 60,
                        },
                        "min_pages_count": {
                            "type": "integer",
                            "description": (
                                "Min competitor sites the phrase must appear on. Default 2. "
                                "A phrase on 1 site is likely accidental."
                            ),
                            "default": 2,
                        },
                        "missing_only": {
                            "type": "boolean",
                            "description": "Only phrases NOT on own page. Default false.",
                            "default": False,
                        },
                        "ngram_type": {
                            "type": "string",
                            "enum":["all", "bigrams", "lemma_trigrams"],
                            "description": "Filter by phrase length. Default 'all'.",
                            "default": "all",
                        },
                    },
                    "required": ["result_id"],
                },
            ),

        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
        try:
            if name == "unihra_health":
                return _ok(client.health())

            elif name == "unihra_analyze":
                _require(arguments, "own_page", "competitors")
                own_page    = arguments["own_page"]
                competitors = arguments["competitors"]

                raw = client.analyze(
                    own_page=own_page,
                    competitors=competitors,
                    queries=arguments.get("queries"),
                    lang=arguments.get("lang", "ru"),
                    url_cookies=arguments.get("url_cookies"),
                    verbose=False,
                )

                result_id = _save_result(raw, own_page, competitors)
                summary   = _build_summary(raw, result_id, own_page, competitors)
                return _ok(summary)

            elif name == "unihra_list_results":
                items =[]
                for p in sorted(_results_dir().glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
                    try:
                        meta = json.loads(p.read_text(encoding="utf-8"))
                        items.append({
                            "result_id":   meta.get("result_id", p.stem),
                            "own_page":    meta.get("own_page"),
                            "competitors": meta.get("competitors"),
                            "saved_at":    meta.get("saved_at"),
                            "file_kb":     round(p.stat().st_size / 1024, 1),
                        })
                    except Exception:
                        continue
                return _ok({"count": len(items), "results": items})

            elif name == "unihra_delete_result":
                _require(arguments, "result_id")
                path = _results_dir() / f"{arguments['result_id']}.json"
                if not path.exists():
                    return _err(f"Result '{arguments['result_id']}' not found.")
                path.unlink()
                return _ok({"deleted": arguments["result_id"]})

            elif name == "unihra_get_page_structure":
                _require(arguments, "result_id")
                data     = _load_result(arguments["result_id"])
                struct   = _strip_junk(data.get("page_structure") or[])
                own_only = arguments.get("own_only", False)

                if own_only and struct:
                    own_page = _load_meta(arguments["result_id"]).get("own_page")
                    struct =[s for s in struct if s.get("url") == own_page] or [struct[0]]

                return _ok({"page_structure": struct})

            elif name == "unihra_get_gaps":
                _require(arguments, "result_id")
                data         = _load_result(arguments["result_id"])
                top_n        = int(arguments.get("top_n", 50))
                min_coverage = float(arguments.get("min_coverage", 20.0))
                min_gap      = float(arguments.get("min_gap", 0.5))
                missing_only = bool(arguments.get("missing_only", False))
                group        = bool(arguments.get("group_by_recommendation", False))

                gaps_raw = (
                    data.get("semantic_context_analysis")
                    or data.get("semantic_context_gaps")
                    or []
                )

                # Filter
                filtered =[]
                for item in gaps_raw:
                    if (item.get("coverage_percent") or 0.0) < min_coverage:
                        continue
                    if (item.get("gap") or 0.0) < min_gap:
                        continue
                    if missing_only and (item.get("own_score") or 0.0) != 0.0:
                        continue
                    filtered.append(_strip_junk(item))

                filtered.sort(key=lambda x: x.get("gap", 0), reverse=True)

                if group:
                    groups: Dict[str, list] = {}
                    for item in filtered:
                        rec = item.get("recommendation") or "Other"
                        groups.setdefault(rec,[]).append(item)
                    # Apply top_n per group
                    groups = {k: v[:top_n] for k, v in groups.items()}
                    return _ok({
                        "result_id":          arguments["result_id"],
                        "total_after_filter": len(filtered),
                        "filters":            {"min_coverage": min_coverage, "min_gap": min_gap, "missing_only": missing_only},
                        "groups":             groups,
                    })
                else:
                    return _ok({
                        "result_id":          arguments["result_id"],
                        "total_after_filter": len(filtered),
                        "returned":           min(top_n, len(filtered)),
                        "filters":            {"min_coverage": min_coverage, "min_gap": min_gap, "missing_only": missing_only},
                        "gaps":               filtered[:top_n],
                    })

            elif name == "unihra_get_anchors":
                _require(arguments, "result_id")
                data         = _load_result(arguments["result_id"])
                top_n        = int(arguments.get("top_n", 50))
                missing_only = bool(arguments.get("missing_only", False))

                anchors_raw = data.get("anchors_analysis") or []

                filtered =[]
                for item in anchors_raw:
                    if missing_only and (item.get("frequency_own") or 0) > 0:
                        continue
                    filtered.append(_strip_junk(item))

                # Sort by competitors avg frequency, then by pages count
                filtered.sort(key=lambda x: (x.get("frequency_comp_avg", 0), x.get("pages_count", 0)), reverse=True)

                return _ok({
                    "result_id":          arguments["result_id"],
                    "total_after_filter": len(filtered),
                    "returned":           min(top_n, len(filtered)),
                    "filters":            {"missing_only": missing_only},
                    "anchors":            filtered[:top_n],
                })

            elif name == "unihra_get_vectors":
                _require(arguments, "result_id")
                data         = _load_result(arguments["result_id"])
                top_n        = int(arguments.get("top_n", 40))
                missing_only = bool(arguments.get("missing_only", True))
                sections_req = arguments.get("sections") or["by_tfidf", "by_frequency"]
                dedupe_gaps  = bool(arguments.get("dedupe_with_gaps", True))

                drmaxs = data.get("drmaxs") or {}

                # Words in gaps (for optional cross-dedup)
                exclude: Set[str] = set()
                if dedupe_gaps:
                    gaps_raw = data.get("semantic_context_analysis") or data.get("semantic_context_gaps") or[]
                    exclude  = {(g.get("lemma") or "").lower() for g in gaps_raw if g.get("lemma")}

                seen: Set[str] = set()
                output: Dict[str, list] = {}

                for key in sections_req:
                    items = drmaxs.get(key)
                    if not isinstance(items, list):
                        continue
                    result_items =[]
                    for item in items:
                        word = (item.get("word") or "").lower()
                        if not word or word in seen or word in exclude:
                            continue
                        if missing_only and item.get("present_on_own_page", False):
                            continue
                        result_items.append(_strip_junk(item))
                        seen.add(word)

                    result_items.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
                    output[key] = result_items[:top_n]

                return _ok({
                    "result_id":              arguments["result_id"],
                    "sections_returned":      list(output.keys()),
                    "deduped_against_gaps":   len(exclude) if dedupe_gaps else 0,
                    "sections":               output,
                })

            elif name == "unihra_get_word_actions":
                _require(arguments, "result_id")
                data          = _load_result(arguments["result_id"])
                action_filter = arguments.get("action", "all")
                top_n         = int(arguments.get("top_n", 50))
                min_freq      = float(arguments.get("min_frequency", 1.0))
                exclude_ok    = bool(arguments.get("exclude_ok", True))

                words_raw = data.get("block_comparison") or []
                groups: Dict[str, list] = {}

                for item in words_raw:
                    if (item.get("frequency") or 0.0) < min_freq:
                        continue
                    raw_action  = item.get("action_needed", "ok")
                    norm_action = _norm_action(raw_action)
                    if exclude_ok and norm_action == "ok":
                        continue
                    cleaned = _strip_junk(item)
                    cleaned["action_needed"] = norm_action
                    groups.setdefault(norm_action,[]).append(cleaned)

                if action_filter != "all":
                    groups = {k: v for k, v in groups.items() if k == action_filter}

                groups = {k: v[:top_n] for k, v in groups.items()}

                return _ok({
                    "result_id":     arguments["result_id"],
                    "action_filter": action_filter,
                    "counts":        {k: len(v) for k, v in groups.items()},
                    "groups":        groups,
                })

            elif name == "unihra_get_ngrams":
                _require(arguments, "result_id")
                data            = _load_result(arguments["result_id"])
                top_n           = int(arguments.get("top_n", 60))
                min_pages_count = int(arguments.get("min_pages_count", 2))
                missing_only    = bool(arguments.get("missing_only", False))
                ngram_type      = arguments.get("ngram_type", "all")

                ngrams_raw = data.get("ngrams_analysis") or data.get("n_grams_analysis") or []

                filtered =[]
                for item in ngrams_raw:
                    if (item.get("pages_count") or 0) < min_pages_count:
                        continue
                    if missing_only and item.get("present_on_own_page", False):
                        continue
                    if ngram_type != "all" and item.get("ngram_type") != ngram_type:
                        continue
                    filtered.append(_strip_junk(item))

                filtered.sort(key=lambda x: x.get("pages_count", 0), reverse=True)

                return _ok({
                    "result_id":          arguments["result_id"],
                    "total_after_filter": len(filtered),
                    "returned":           min(top_n, len(filtered)),
                    "filters": {
                        "min_pages_count": min_pages_count,
                        "missing_only":    missing_only,
                        "ngram_type":      ngram_type,
                    },
                    "ngrams": filtered[:top_n],
                })

            else:
                return _err(f"Unknown tool: '{name}'")

        except (ValueError, UnihraError) as exc:
            return _err(str(exc))
        except Exception as exc:  # noqa: BLE001
            return _err(f"Unexpected error in '{name}': {exc}\n{traceback.format_exc()}")

    return server

def _ok(data: Any) -> list[mcp_types.TextContent]:
    return[mcp_types.TextContent(
        type="text",
        text=json.dumps(data, ensure_ascii=False, indent=2),
    )]


def _err(msg: str) -> list[mcp_types.TextContent]:
    return[mcp_types.TextContent(
        type="text",
        text=json.dumps({"error": msg}, ensure_ascii=False),
    )]


def _require(arguments: dict, *keys: str) -> None:
    for k in keys:
        if not arguments.get(k):
            raise ValueError(f"Required argument '{k}' is missing or empty.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unihra MCP Server — file-backed SEO & Semantic Analysis over MCP."
    )
    parser.add_argument("--key",         default=None, help="API key (or UNIHRA_API_KEY env var).")
    parser.add_argument("--retries",     type=int, default=3, help="HTTP retries. Default: 3.")
    parser.add_argument("--base-url",    default="https://unihra.ru", help="API base URL.")
    parser.add_argument("--results-dir", default=None, help="Directory to store results (overrides UNIHRA_RESULTS_DIR).")
    args = parser.parse_args()

    if args.results_dir:
        os.environ["UNIHRA_RESULTS_DIR"] = args.results_dir

    api_key = args.key or os.getenv("UNIHRA_API_KEY")
    if not api_key:
        print(
            "ERROR: API key required.\n"
            "  Pass --key YOUR_KEY  or  set UNIHRA_API_KEY environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = UnihraClient(api_key=api_key, base_url=args.base_url, max_retries=args.retries)
    server = build_server(client)

    import asyncio

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()