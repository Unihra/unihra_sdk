import asyncio
import importlib
import json
import pathlib
import sys
import types

import pytest


class FakeTextContent:
    def __init__(self, type, text):
        self.type = type
        self.text = text


class FakeTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


class FakeServer:
    def __init__(self, name):
        self.name = name
        self._list_tools_handler = None
        self._call_tool_handler = None

    def list_tools(self):
        def decorator(func):
            self._list_tools_handler = func
            return func
        return decorator

    def call_tool(self):
        def decorator(func):
            self._call_tool_handler = func
            return func
        return decorator

    def create_initialization_options(self):
        return {}

    async def run(self, read_stream, write_stream, options):
        return None


class FakeClient:
    def health(self):
        return {"status": "ok"}

    def analyze(self, **kwargs):
        return {
            "block_comparison": [{"word": "price", "action_needed": "Добавить"}],
            "semantic_context_analysis": [{"lemma": "battery", "gap": 10.5, "own_score": 0.0}],
            "drmaxs": {"by_frequency": [{"word": "logistics", "similarity_score": 0.89, "present_on_own_page": False}]},
            "page_structure": [{"url": kwargs.get("own_page")}],
        }

    def analyze_stream(self, **kwargs):
        yield {"state": "PROGRESS", "progress": 50}
        yield {"state": "SUCCESS", "result": {"ok": True}}

    def get_page_structure(self, task_id):
        return [{"url": "https://example.com", "task_id": task_id}]


@pytest.fixture
def mcp_server_module(monkeypatch):
    project_root = pathlib.Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(project_root / "src"))

    for module_name in list(sys.modules.keys()):
        if module_name == "unihra" or module_name.startswith("unihra."):
            sys.modules.pop(module_name)

    fake_mcp = types.ModuleType("mcp")
    fake_mcp_types = types.ModuleType("mcp.types")
    fake_mcp_types.TextContent = FakeTextContent
    fake_mcp_types.Tool = FakeTool

    fake_mcp_server = types.ModuleType("mcp.server")
    fake_mcp_server.Server = FakeServer

    fake_mcp_stdio = types.ModuleType("mcp.server.stdio")

    class _DummyContext:
        async def __aenter__(self):
            return object(), object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def stdio_server():
        return _DummyContext()

    fake_mcp_stdio.stdio_server = stdio_server
    fake_mcp.types = fake_mcp_types
    fake_mcp.server = fake_mcp_server

    monkeypatch.setitem(sys.modules, "mcp", fake_mcp)
    monkeypatch.setitem(sys.modules, "mcp.types", fake_mcp_types)
    monkeypatch.setitem(sys.modules, "mcp.server", fake_mcp_server)
    monkeypatch.setitem(sys.modules, "mcp.server.stdio", fake_mcp_stdio)

    module = importlib.import_module("unihra.mcp_server")
    return importlib.reload(module)


def _tool_result_payload(result):
    assert isinstance(result, list)
    assert result
    content = result[0]
    assert content.type == "text"
    return json.loads(content.text)


def test_build_server_registers_tools(mcp_server_module):
    server = mcp_server_module.build_server(FakeClient())
    tools = asyncio.run(server._list_tools_handler())
    names = [tool.name for tool in tools]

    assert "unihra_health" in names
    assert "unihra_analyze" in names
    assert "unihra_word_actions" in names


def test_call_tool_health(mcp_server_module):
    server = mcp_server_module.build_server(FakeClient())
    result = asyncio.run(server._call_tool_handler("unihra_health", {}))
    payload = _tool_result_payload(result)
    assert payload["status"] == "ok"


def test_call_tool_analyze_stream_events(mcp_server_module):
    server = mcp_server_module.build_server(FakeClient())
    result = asyncio.run(server._call_tool_handler(
        "unihra_analyze_stream_events",
        {"own_page": "https://my.site", "competitors": ["https://comp.site"]},
    ))
    payload = _tool_result_payload(result)

    assert isinstance(payload, list)
    assert payload[-1]["state"] == "SUCCESS"


def test_call_tool_word_actions_maps_russian_labels(mcp_server_module):
    server = mcp_server_module.build_server(FakeClient())
    analyze_result = {
        "block_comparison": [
            {"word": "price", "action_needed": "Добавить"},
            {"word": "stock", "action_needed": "Ок"},
        ]
    }
    result = asyncio.run(server._call_tool_handler(
        "unihra_word_actions",
        {"result": analyze_result, "action": "all"},
    ))
    payload = _tool_result_payload(result)

    assert payload["counts"]["add"] == 1
    assert payload["counts"]["ok"] == 1


def test_call_tool_extract_section_alias(mcp_server_module):
    server = mcp_server_module.build_server(FakeClient())
    analyze_result = {
        "semantic_context_gaps": [{"lemma": "battery", "gap": 10.5}]
    }
    result = asyncio.run(server._call_tool_handler(
        "unihra_extract_section",
        {"result": analyze_result, "section": "semantic_context_analysis"},
    ))
    payload = _tool_result_payload(result)

    assert "semantic_context_analysis" in payload
    assert payload["semantic_context_analysis"][0]["lemma"] == "battery"
