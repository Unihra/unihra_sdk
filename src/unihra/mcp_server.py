import argparse
import asyncio
import json
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

from .client import ACTION_MAP, UnihraClient
from .exceptions import UnihraError

try:
    from mcp import types as mcp_types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print(
        "ERROR: 'mcp' package not found.\n"
        "Install it with: pip install mcp\n"
        "Or install extra: pip install unihra[mcp]",
        file=sys.stderr
    )
    sys.exit(1)


def _ok(data: Any) -> List[mcp_types.TextContent]:
    return [mcp_types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def _err(message: str) -> List[mcp_types.TextContent]:
    return [mcp_types.TextContent(type="text", text=json.dumps({"error": message}, ensure_ascii=False))]


def _require(arguments: Dict[str, Any], *keys: str):
    for key in keys:
        if not arguments.get(key):
            raise ValueError(f"Required argument '{key}' is missing or empty.")


def _extract_section_data(result: Dict[str, Any], section: str):
    alias_map = {
        "semantic_context_analysis": ["semantic_context_analysis", "semantic_context_gaps"],
        "ngrams_analysis": ["ngrams_analysis", "n_grams_analysis"],
    }
    keys_to_try = alias_map.get(section, [section])

    for key in keys_to_try:
        if key in result:
            return result[key]
    return None


def build_server(client: UnihraClient) -> Server:
    server = Server("unihra-mcp")

    @server.list_tools()
    async def list_tools() -> List[mcp_types.Tool]:
        return [
            mcp_types.Tool(
                name="unihra_health",
                description="Check Unihra API availability.",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            mcp_types.Tool(
                name="unihra_analyze",
                description=(
                    "Run full SEO and semantic analysis for a target page and competitors. "
                    "Returns all blocks including page structure, semantic gaps, words, ngrams and vectors."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "own_page": {"type": "string", "description": "Target page URL."},
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Competitor URLs list.",
                        },
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target queries for context recommendations.",
                        },
                        "lang": {
                            "type": "string",
                            "enum": ["ru", "en"],
                            "description": "Language. Default: ru.",
                        },
                        "url_cookies": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "description": "Optional map URL -> cookies string.",
                        },
                    },
                    "required": ["own_page", "competitors"],
                },
            ),
            mcp_types.Tool(
                name="unihra_analyze_stream_events",
                description="Run analysis and return all SSE events as a JSON array.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "own_page": {"type": "string", "description": "Target page URL."},
                        "competitors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Competitor URLs list.",
                        },
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target queries (optional).",
                        },
                        "lang": {
                            "type": "string",
                            "enum": ["ru", "en"],
                            "description": "Language. Default: ru.",
                        },
                        "url_cookies": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                            "description": "Optional map URL -> cookies string.",
                        },
                    },
                    "required": ["own_page", "competitors"],
                },
            ),
            mcp_types.Tool(
                name="unihra_get_page_structure",
                description="Get page structure report by task_id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task id from completed analysis."},
                    },
                    "required": ["task_id"],
                },
            ),
            mcp_types.Tool(
                name="unihra_extract_section",
                description="Extract one section from analysis result.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object", "description": "Full analysis result."},
                        "section": {
                            "type": "string",
                            "enum": [
                                "page_structure",
                                "semantic_context_analysis",
                                "block_comparison",
                                "ngrams_analysis",
                                "drmaxs",
                            ],
                            "description": "Result section key.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Optional list limit.",
                        },
                    },
                    "required": ["result", "section"],
                },
            ),
            mcp_types.Tool(
                name="unihra_summarize_gaps",
                description="Group semantic gaps by recommendation and sort by gap desc.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object", "description": "Full analysis result."},
                        "top_n": {"type": "integer", "description": "Top rows per recommendation. Default: 10."},
                        "missing_only": {"type": "boolean", "description": "Include only rows with own_score == 0."},
                    },
                    "required": ["result"],
                },
            ),
            mcp_types.Tool(
                name="unihra_summarize_vectors",
                description="Summarize drmaxs vectors grouped by subsection.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object", "description": "Full analysis result."},
                        "top_n": {"type": "integer", "description": "Top rows per vector group. Default: 20."},
                        "missing_only": {"type": "boolean", "description": "Include only words absent on own page."},
                    },
                    "required": ["result"],
                },
            ),
            mcp_types.Tool(
                name="unihra_word_actions",
                description="Group block_comparison by action_needed: add/increase/decrease/ok.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "object", "description": "Full analysis result."},
                        "action": {
                            "type": "string",
                            "enum": ["add", "increase", "decrease", "ok", "all"],
                            "description": "Action filter. Default: all.",
                        },
                        "top_n": {"type": "integer", "description": "Optional max items per group."},
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
                result = client.analyze(
                    own_page=arguments["own_page"],
                    competitors=arguments["competitors"],
                    queries=arguments.get("queries"),
                    lang=arguments.get("lang", "ru"),
                    url_cookies=arguments.get("url_cookies"),
                    verbose=False,
                )
                return _ok(result)

            if name == "unihra_analyze_stream_events":
                _require(arguments, "own_page", "competitors")
                events = []
                for event in client.analyze_stream(
                    own_page=arguments["own_page"],
                    competitors=arguments["competitors"],
                    queries=arguments.get("queries"),
                    lang=arguments.get("lang", "ru"),
                    url_cookies=arguments.get("url_cookies"),
                ):
                    events.append(event)
                return _ok(events)

            if name == "unihra_get_page_structure":
                _require(arguments, "task_id")
                return _ok(client.get_page_structure(arguments["task_id"]))

            if name == "unihra_extract_section":
                _require(arguments, "result", "section")
                result = arguments["result"]
                section = arguments["section"]
                limit = arguments.get("limit")

                data = _extract_section_data(result, section)
                if data is None:
                    return _err(
                        f"Section '{section}' not found in result. "
                        f"Available keys: {list(result.keys())}"
                    )

                if isinstance(data, list) and isinstance(limit, int) and limit > 0:
                    data = data[:limit]
                return _ok({section: data})

            if name == "unihra_summarize_gaps":
                _require(arguments, "result")
                result = arguments["result"]
                top_n = arguments.get("top_n", 10)
                missing_only = arguments.get("missing_only", False)

                gaps = result.get("semantic_context_analysis") or result.get("semantic_context_gaps") or []
                if not gaps:
                    return _ok({"message": "No semantic_context_analysis data in result.", "groups": {}})

                if missing_only:
                    gaps = [item for item in gaps if (item.get("own_score") or 0.0) == 0.0]

                gaps_sorted = sorted(gaps, key=lambda x: x.get("gap", 0), reverse=True)
                groups = {}
                for item in gaps_sorted:
                    recommendation = item.get("recommendation") or "Other"
                    groups.setdefault(recommendation, [])
                    if len(groups[recommendation]) < top_n:
                        groups[recommendation].append({
                            "lemma": item.get("lemma"),
                            "gap": item.get("gap"),
                            "coverage_percent": item.get("coverage_percent"),
                            "own_score": item.get("own_score"),
                            "context_snippet": item.get("context_snippet"),
                        })

                return _ok({
                    "total_gaps": len(gaps),
                    "missing_only_filter": missing_only,
                    "top_n_per_group": top_n,
                    "groups": groups,
                })

            if name == "unihra_summarize_vectors":
                _require(arguments, "result")
                result = arguments["result"]
                top_n = arguments.get("top_n", 20)
                missing_only = arguments.get("missing_only", True)

                drmaxs = result.get("drmaxs") or {}
                if not drmaxs:
                    return _ok({"message": "No drmaxs (Vector AI) data in result.", "sections": {}})

                output = {}
                for sub_key, items in drmaxs.items():
                    if not isinstance(items, list):
                        continue
                    filtered = items
                    if missing_only:
                        filtered = [item for item in items if not item.get("present_on_own_page", True)]

                    sorted_items = sorted(
                        filtered,
                        key=lambda x: x.get("similarity_score", 0),
                        reverse=True
                    )
                    output[sub_key] = sorted_items[:top_n]

                return _ok({
                    "missing_only_filter": missing_only,
                    "top_n": top_n,
                    "sections": output,
                })

            if name == "unihra_word_actions":
                _require(arguments, "result")
                result = arguments["result"]
                action_filter = arguments.get("action", "all")
                top_n = arguments.get("top_n")

                words = result.get("block_comparison") or []
                if not words:
                    return _ok({"message": "No block_comparison data in result.", "groups": {}})

                groups = {}
                for item in words:
                    raw_action = item.get("action_needed", "ok")
                    normalized_action = ACTION_MAP.get(raw_action, raw_action).lower()
                    groups.setdefault(normalized_action, []).append(item)

                if action_filter != "all":
                    groups = {key: values for key, values in groups.items() if key == action_filter}
                if isinstance(top_n, int) and top_n > 0:
                    groups = {key: values[:top_n] for key, values in groups.items()}

                return _ok({
                    "action_filter": action_filter,
                    "counts": {key: len(values) for key, values in groups.items()},
                    "groups": groups,
                })

            return _err(f"Unknown tool: '{name}'")
        except (ValueError, UnihraError) as exc:
            return _err(str(exc))
        except Exception as exc:
            return _err(f"Unexpected error: {exc}\n{traceback.format_exc()}")

    return server


def main():
    parser = argparse.ArgumentParser(description="Unihra MCP Server")
    parser.add_argument("--key", help="API key (or set UNIHRA_API_KEY env var)")
    parser.add_argument("--retries", type=int, default=3, help="Max retries for connection stability")
    parser.add_argument("--base-url", default="https://unihra.ru", help="Override API base URL")
    args = parser.parse_args()

    api_key = args.key or os.getenv("UNIHRA_API_KEY")
    if not api_key:
        print(
            "Error: API key required. Pass --key or set UNIHRA_API_KEY env var.",
            file=sys.stderr
        )
        sys.exit(1)

    client = UnihraClient(api_key=api_key, base_url=args.base_url, max_retries=args.retries)
    server = build_server(client)

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
