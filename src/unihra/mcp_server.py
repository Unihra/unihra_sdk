"""
Unihra MCP Server — exposes the Unihra SDK as Model Context Protocol tools.

When the user asks to compare pages, find SEO gaps, audit content, or tune
Title/H1/H2, agents should call ``unihra_analyze`` (not ad-hoc HTTP parsing).

Run::

    UNIHRA_API_KEY=your_key python -m unihra.mcp_server
    python -m unihra.mcp_server --key YOUR_KEY [--retries 3] [--base-url https://unihra.ru]

Cursor / Claude MCP JSON (example)::

    {
      "mcpServers": {
        "unihra": {
          "command": "python",
          "args": ["-m", "unihra.mcp_server"],
          "env": { "UNIHRA_API_KEY": "YOUR_KEY_HERE" }
        }
      }
    }
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import traceback
from typing import Any, Dict, List, Optional, Set

try:
    from mcp import types as mcp_types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
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

# Technical fields removed from payloads before returning to the LLM
_JUNK_FIELDS: Set[str] = {
    "id",
    "block_id",
    "analysis_id",
    "task_id",
    "created_at",
    "updated_at",
    "modified_at",
}

_ACTION_MAP: Dict[str, str] = {
    "Добавить": "add",
    "Увеличить": "increase",
    "Уменьшить": "decrease",
    "Ок": "ok",
    "Ничего не делать": "ok",
    "add": "add",
    "increase": "increase",
    "decrease": "decrease",
    "ok": "ok",
}


def _strip_junk(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_junk(v) for k, v in obj.items() if k not in _JUNK_FIELDS}
    if isinstance(obj, list):
        return [_strip_junk(item) for item in obj]
    return obj


def _clean_block_comparison(
    items: List[dict],
    min_frequency: float = 2.0,
    include_ok: bool = False,
) -> List[dict]:
    result = []
    for item in items:
        raw_action = item.get("action_needed", "ok")
        norm_action = _ACTION_MAP.get(str(raw_action), str(raw_action)).lower()
        if not include_ok and norm_action == "ok":
            continue
        if (item.get("frequency") or 0.0) < min_frequency:
            continue
        cleaned = _strip_junk(item)
        cleaned["action_needed"] = norm_action
        result.append(cleaned)
    return result


def _clean_semantic_gaps(
    items: List[dict],
    top_n: int = 50,
    min_coverage: float = 25.0,
    min_gap: float = 1.0,
    missing_only: bool = False,
) -> List[dict]:
    filtered = []
    for item in items:
        if (item.get("coverage_percent") or 0.0) < min_coverage:
            continue
        if (item.get("gap") or 0.0) < min_gap:
            continue
        if missing_only and (item.get("own_score") or 0.0) != 0.0:
            continue
        filtered.append(_strip_junk(item))

    filtered.sort(key=lambda x: x.get("gap", 0), reverse=True)
    return filtered[:top_n]


def _clean_ngrams(
    items: List[dict],
    min_pages_count: int = 3,
    min_frequency_avg: float = 1.5,
) -> List[dict]:
    result = []
    for item in items:
        if (item.get("pages_count") or 0) < min_pages_count:
            continue
        if (item.get("frequency_avg") or 0.0) < min_frequency_avg:
            continue
        result.append(_strip_junk(item))
    return result


def _clean_drmaxs(
    drmaxs: dict,
    top_n: int = 30,
    missing_only: bool = True,
    include_sites_count: bool = False,
    exclude_words: Optional[Set[str]] = None,
) -> dict:
    exclude_words = exclude_words or set()
    seen_words: Set[str] = set()
    output: Dict[str, List[dict]] = {}

    section_order = ["by_tfidf", "by_frequency"]
    if include_sites_count:
        section_order.append("by_sites_count")

    for key in section_order:
        items = drmaxs.get(key)
        if not isinstance(items, list):
            continue

        filtered = []
        for item in items:
            word = (item.get("word") or "").lower()
            if not word:
                continue
            if word in seen_words or word in exclude_words:
                continue
            if missing_only and item.get("present_on_own_page", False):
                continue
            filtered.append(_strip_junk(item))
            seen_words.add(word)

        filtered.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        output[key] = filtered[:top_n]

    return output


def _extract_semantic_words(gaps: List[dict]) -> Set[str]:
    return {(item.get("lemma") or "").lower() for item in gaps if item.get("lemma")}


def _ok(data: Any) -> List[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps(data, ensure_ascii=False, indent=2),
        )
    ]


def _err(message: str) -> List[mcp_types.TextContent]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps({"error": message}, ensure_ascii=False),
        )
    ]


def _require(arguments: Dict[str, Any], *keys: str) -> None:
    for k in keys:
        if not arguments.get(k):
            raise ValueError(f"Required argument '{k}' is missing or empty.")


def _build_clean_result(
    raw: dict,
    *,
    gaps_top_n: int,
    gaps_min_coverage: float,
    gaps_min_gap: float,
    gaps_missing_only: bool,
    blocks_min_freq: float,
    blocks_include_ok: bool,
    ngrams_min_pages: int,
    vectors_top_n: int,
    vectors_missing: bool,
    vectors_sites_count: bool,
) -> dict:
    page_structure = _strip_junk(raw.get("page_structure") or [])

    gaps_raw = (
        raw.get("semantic_context_analysis")
        or raw.get("semantic_context_gaps")
        or []
    )
    gaps_cleaned = _clean_semantic_gaps(
        gaps_raw,
        top_n=gaps_top_n,
        min_coverage=gaps_min_coverage,
        min_gap=gaps_min_gap,
        missing_only=gaps_missing_only,
    )

    blocks_cleaned = _clean_block_comparison(
        raw.get("block_comparison") or [],
        min_frequency=blocks_min_freq,
        include_ok=blocks_include_ok,
    )

    ngrams_cleaned = _clean_ngrams(
        raw.get("ngrams_analysis") or raw.get("n_grams_analysis") or [],
        min_pages_count=ngrams_min_pages,
    )
    ngrams_cleaned.sort(key=lambda x: x.get("pages_count", 0), reverse=True)

    exclude_words = _extract_semantic_words(gaps_cleaned)
    drmaxs_cleaned = _clean_drmaxs(
        raw.get("drmaxs") or {},
        top_n=vectors_top_n,
        missing_only=vectors_missing,
        include_sites_count=vectors_sites_count,
        exclude_words=exclude_words,
    )

    return {
        "page_structure": page_structure,
        "semantic_context_analysis": gaps_cleaned,
        "block_comparison": blocks_cleaned,
        "ngrams_analysis": ngrams_cleaned,
        "drmaxs": drmaxs_cleaned,
        "_meta": {
            "gaps_returned": len(gaps_cleaned),
            "blocks_returned": len(blocks_cleaned),
            "ngrams_returned": len(ngrams_cleaned),
            "filters_applied": {
                "gaps_top_n": gaps_top_n,
                "gaps_min_coverage": gaps_min_coverage,
                "gaps_min_gap": gaps_min_gap,
                "gaps_missing_only": gaps_missing_only,
                "blocks_min_freq": blocks_min_freq,
                "blocks_include_ok": blocks_include_ok,
                "ngrams_min_pages": ngrams_min_pages,
                "vectors_top_n": vectors_top_n,
                "vectors_missing": vectors_missing,
            },
        },
    }


def build_server(client: UnihraClient) -> Server:
    server = Server("unihra-mcp")

    @server.list_tools()
    async def list_tools() -> List[mcp_types.Tool]:
        return [
            mcp_types.Tool(
                name="unihra_health",
                description=(
                    "Check Unihra API availability. "
                    "Call before analyses to verify the service is reachable."
                ),
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            mcp_types.Tool(
                name="unihra_analyze",
                description=(
                    "PRIMARY tool for SEO content analysis and page comparison. "
                    "Use instead of ad-hoc page fetching when comparing URLs, gaps, "
                    "Title/H1, or LSI words. Returns cleaned blocks plus _meta. "
                    "Default filters reduce noise (coverage/gap thresholds, min frequency, etc.)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "own_page": {"type": "string", "description": "URL of the page to optimise."},
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Competitor URLs (1–10 recommended).",
                        },
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target queries for zone recommendations.",
                        },
                        "lang": {"type": "string", "enum": ["ru", "en"], "description": "Language. Default: ru."},
                        "url_cookies": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "description": "URL -> cookie string for gated pages.",
                        },
                        "gaps_top_n": {"type": "integer", "description": "Max gap rows. Default 50.", "default": 50},
                        "gaps_min_coverage": {
                            "type": "number",
                            "description": "Min competitor coverage % for gaps. Default 25.",
                            "default": 25.0,
                        },
                        "gaps_min_gap": {"type": "number", "description": "Min gap value. Default 1.0.", "default": 1.0},
                        "gaps_missing_only": {
                            "type": "boolean",
                            "description": "Only words with own_score == 0. Default false.",
                            "default": False,
                        },
                        "blocks_min_frequency": {
                            "type": "number",
                            "description": "Min TF frequency for block_comparison. Default 2.0.",
                            "default": 2.0,
                        },
                        "blocks_include_ok": {
                            "type": "boolean",
                            "description": "Include action ok in block_comparison. Default false.",
                            "default": False,
                        },
                        "ngrams_min_pages": {
                            "type": "integer",
                            "description": "Min competitor pages for n-gram. Default 3.",
                            "default": 3,
                        },
                        "vectors_top_n": {"type": "integer", "description": "Max LSI words per section. Default 30.", "default": 30},
                        "vectors_missing_only": {
                            "type": "boolean",
                            "description": "Only LSI words absent on own page. Default true.",
                            "default": True,
                        },
                        "vectors_include_sites_count": {
                            "type": "boolean",
                            "description": "Include drmaxs by_sites_count. Default false.",
                            "default": False,
                        },
                    },
                    "required": ["own_page", "competitors"],
                },
            ),
            mcp_types.Tool(
                name="unihra_analyze_stream_events",
                description=(
                    "Stream all SSE events for a run. Use for progress or raw task_id. "
                    "Events are passed through _strip_junk only."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "own_page": {"type": "string"},
                        "competitors": {"type": "array", "items": {"type": "string"}},
                        "queries": {"type": "array", "items": {"type": "string"}},
                        "lang": {"type": "string", "enum": ["ru", "en"]},
                        "url_cookies": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                    "required": ["own_page", "competitors"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_page_structure",
                description="GET /report/structure/{task_id} — headings, meta, metrics per URL.",
                inputSchema={
                    "type": "object",
                    "properties": {"task_id": {"type": "string"}},
                    "required": ["task_id"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_gaps",
                description="Re-group semantic gaps from an existing analyze result by recommendation.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object"},
                        "top_n": {"type": "integer", "default": 10},
                        "min_coverage": {"type": "number", "default": 25.0},
                        "min_gap": {"type": "number", "default": 1.0},
                        "missing_only": {"type": "boolean", "default": False},
                    },
                    "required": ["result"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_vectors",
                description="LSI / DrMaxs vectors from an existing result with dedup vs gaps.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object"},
                        "top_n": {"type": "integer", "default": 30},
                        "missing_only": {"type": "boolean", "default": True},
                        "include_sites_count": {"type": "boolean", "default": False},
                    },
                    "required": ["result"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_word_actions",
                description="Group block_comparison by action (add/increase/decrease/ok).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object"},
                        "action": {
                            "type": "string",
                            "enum": ["add", "increase", "decrease", "ok", "all"],
                            "default": "all",
                        },
                        "top_n": {"type": "integer"},
                        "min_frequency": {"type": "number", "default": 2.0},
                    },
                    "required": ["result"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_ngrams",
                description="Filter n-grams from an existing result.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object"},
                        "missing_only": {"type": "boolean", "default": False},
                        "min_pages_count": {"type": "integer", "default": 3},
                        "ngram_type": {
                            "type": "string",
                            "enum": ["all", "bigrams", "lemma_trigrams"],
                            "default": "all",
                        },
                        "top_n": {"type": "integer"},
                    },
                    "required": ["result"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[mcp_types.TextContent]:
        try:
            if name == "unihra_health":
                return _ok(client.health())

            if name == "unihra_analyze":
                _require(arguments, "own_page", "competitors")

                gaps_top_n = int(arguments.get("gaps_top_n", 50))
                gaps_min_coverage = float(arguments.get("gaps_min_coverage", 25.0))
                gaps_min_gap = float(arguments.get("gaps_min_gap", 1.0))
                gaps_missing_only = bool(arguments.get("gaps_missing_only", False))
                blocks_min_freq = float(arguments.get("blocks_min_frequency", 2.0))
                blocks_include_ok = bool(arguments.get("blocks_include_ok", False))
                ngrams_min_pages = int(arguments.get("ngrams_min_pages", 3))
                vectors_top_n = int(arguments.get("vectors_top_n", 30))
                vectors_missing = bool(arguments.get("vectors_missing_only", True))
                vectors_sites_count = bool(arguments.get("vectors_include_sites_count", False))

                raw = client.analyze(
                    own_page=arguments["own_page"],
                    competitors=arguments["competitors"],
                    queries=arguments.get("queries"),
                    lang=arguments.get("lang", "ru"),
                    url_cookies=arguments.get("url_cookies"),
                    verbose=False,
                )

                return _ok(
                    _build_clean_result(
                        raw,
                        gaps_top_n=gaps_top_n,
                        gaps_min_coverage=gaps_min_coverage,
                        gaps_min_gap=gaps_min_gap,
                        gaps_missing_only=gaps_missing_only,
                        blocks_min_freq=blocks_min_freq,
                        blocks_include_ok=blocks_include_ok,
                        ngrams_min_pages=ngrams_min_pages,
                        vectors_top_n=vectors_top_n,
                        vectors_missing=vectors_missing,
                        vectors_sites_count=vectors_sites_count,
                    )
                )

            if name == "unihra_analyze_stream_events":
                _require(arguments, "own_page", "competitors")
                events: List[Dict[str, Any]] = []
                for event in client.analyze_stream(
                    own_page=arguments["own_page"],
                    competitors=arguments["competitors"],
                    queries=arguments.get("queries"),
                    lang=arguments.get("lang", "ru"),
                    url_cookies=arguments.get("url_cookies"),
                ):
                    events.append(_strip_junk(event))
                return _ok(events)

            if name == "unihra_get_page_structure":
                _require(arguments, "task_id")
                structure = client.get_page_structure(arguments["task_id"])
                return _ok(_strip_junk(structure))

            if name == "unihra_get_gaps":
                _require(arguments, "result")
                raw_result: dict = arguments["result"]
                top_n = int(arguments.get("top_n", 10))
                min_coverage = float(arguments.get("min_coverage", 25.0))
                min_gap = float(arguments.get("min_gap", 1.0))
                missing_only = bool(arguments.get("missing_only", False))

                gaps_raw = (
                    raw_result.get("semantic_context_analysis")
                    or raw_result.get("semantic_context_gaps")
                    or []
                )
                gaps = _clean_semantic_gaps(
                    gaps_raw,
                    top_n=top_n * 50,
                    min_coverage=min_coverage,
                    min_gap=min_gap,
                    missing_only=missing_only,
                )

                groups: Dict[str, List[dict]] = {}
                for item in gaps:
                    rec = item.get("recommendation") or "Other"
                    bucket = groups.setdefault(rec, [])
                    if len(bucket) < top_n:
                        bucket.append(
                            {
                                "lemma": item.get("lemma"),
                                "gap": item.get("gap"),
                                "coverage_percent": item.get("coverage_percent"),
                                "own_score": item.get("own_score"),
                                "context_snippet": item.get("context_snippet"),
                            }
                        )

                return _ok(
                    {
                        "total_after_filter": len(gaps),
                        "top_n_per_group": top_n,
                        "filters": {
                            "missing_only": missing_only,
                            "min_coverage": min_coverage,
                            "min_gap": min_gap,
                        },
                        "groups": groups,
                    }
                )

            if name == "unihra_get_vectors":
                _require(arguments, "result")
                raw_result: dict = arguments["result"]
                top_n = int(arguments.get("top_n", 30))
                missing_only = bool(arguments.get("missing_only", True))
                include_sites = bool(arguments.get("include_sites_count", False))

                drmaxs = raw_result.get("drmaxs") or {}
                gaps_raw = (
                    raw_result.get("semantic_context_analysis")
                    or raw_result.get("semantic_context_gaps")
                    or []
                )
                exclude_words = _extract_semantic_words(gaps_raw)

                cleaned = _clean_drmaxs(
                    drmaxs,
                    top_n=top_n,
                    missing_only=missing_only,
                    include_sites_count=include_sites,
                    exclude_words=exclude_words,
                )

                return _ok(
                    {
                        "filters": {
                            "missing_only": missing_only,
                            "top_n_per_section": top_n,
                            "cross_dedup_gap_words": len(exclude_words),
                        },
                        "sections": cleaned,
                    }
                )

            if name == "unihra_get_word_actions":
                _require(arguments, "result")
                raw_result: dict = arguments["result"]
                action_filter = arguments.get("action", "all")
                top_n: Optional[int] = arguments.get("top_n")
                min_frequency = float(arguments.get("min_frequency", 2.0))

                words_raw = raw_result.get("block_comparison") or []
                cleaned = _clean_block_comparison(
                    words_raw,
                    min_frequency=min_frequency,
                    include_ok=True,
                )

                groups: Dict[str, List[dict]] = {}
                for item in cleaned:
                    action = item.get("action_needed", "ok")
                    groups.setdefault(action, []).append(item)

                if action_filter != "all":
                    groups = {k: v for k, v in groups.items() if k == action_filter}

                if top_n:
                    groups = {k: v[:top_n] for k, v in groups.items()}

                return _ok(
                    {
                        "action_filter": action_filter,
                        "counts": {k: len(v) for k, v in groups.items()},
                        "groups": groups,
                    }
                )

            if name == "unihra_get_ngrams":
                _require(arguments, "result")
                raw_result: dict = arguments["result"]
                missing_only = bool(arguments.get("missing_only", False))
                min_pages_count = int(arguments.get("min_pages_count", 3))
                ngram_type = arguments.get("ngram_type", "all")
                top_n: Optional[int] = arguments.get("top_n")

                ngrams_raw = (
                    raw_result.get("ngrams_analysis")
                    or raw_result.get("n_grams_analysis")
                    or []
                )
                cleaned = _clean_ngrams(
                    ngrams_raw,
                    min_pages_count=min_pages_count,
                    min_frequency_avg=1.5,
                )

                if missing_only:
                    cleaned = [n for n in cleaned if not n.get("present_on_own_page", False)]

                if ngram_type != "all":
                    cleaned = [n for n in cleaned if n.get("ngram_type") == ngram_type]

                cleaned.sort(key=lambda x: x.get("pages_count", 0), reverse=True)

                if top_n:
                    cleaned = cleaned[:top_n]

                return _ok(
                    {
                        "total_after_filter": len(cleaned),
                        "filters": {
                            "missing_only": missing_only,
                            "min_pages_count": min_pages_count,
                            "ngram_type": ngram_type,
                        },
                        "ngrams": cleaned,
                    }
                )

            return _err(f"Unknown tool: '{name}'")

        except (ValueError, UnihraError) as exc:
            return _err(str(exc))
        except Exception as exc:
            return _err(f"Unexpected error: {exc}\n{traceback.format_exc()}")

    return server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unihra MCP Server — SEO and semantic analysis for LLM agents."
    )
    parser.add_argument("--key", default=None, help="API key or set UNIHRA_API_KEY")
    parser.add_argument("--retries", type=int, default=3, help="Max HTTP retries (default 3)")
    parser.add_argument("--base-url", default="https://unihra.ru", help="API base URL")
    args = parser.parse_args()

    api_key = args.key or os.getenv("UNIHRA_API_KEY")
    if not api_key:
        print(
            "ERROR: Unihra API key not provided.\n"
            "  Pass --key YOUR_KEY  or  set UNIHRA_API_KEY.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = UnihraClient(api_key=api_key, base_url=args.base_url, max_retries=args.retries)
    server = build_server(client)

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(_run())


if __name__ == "__main__":
    main()
