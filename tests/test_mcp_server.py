import asyncio
import importlib
import json
import os
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
        self._call_tool_handler = None
    def list_tools(self):
        def decorator(func): return func
        return decorator
    def call_tool(self):
        def decorator(func): self._call_tool_handler = func; return func
        return decorator
    def create_initialization_options(self): return {}
    async def run(self, r, w, opt): return None

mcp_mock = types.ModuleType("mcp")
mcp_mock.server = types.ModuleType("mcp.server")
mcp_mock.server.Server = FakeServer
mcp_mock.server.stdio = types.ModuleType("mcp.server.stdio")
mcp_mock.server.stdio.stdio_server = lambda: type("_D", (), {"__aenter__": lambda s: (object(), object()), "__aexit__": lambda s, *a: None})()
mcp_mock.types = types.ModuleType("mcp.types")
mcp_mock.types.TextContent = FakeTextContent
mcp_mock.types.Tool = FakeTool

sys.modules["mcp"] = mcp_mock
sys.modules["mcp.types"] = mcp_mock.types
sys.modules["mcp.server"] = mcp_mock.server
sys.modules["mcp.server.stdio"] = mcp_mock.server.stdio

class FakeClient:
    def __init__(self, storage_path):
        self.storage_path = storage_path
    
    def analyze(self, **kwargs):
        return {
            "anchors_analysis":[
                {
                    "anchor": "купить", 
                    "frequency_own": 0, 
                    "frequency_comp_avg": 5.0, 
                    "pages_count": 3
                }
            ],
            "semantic_context_analysis": [],
            "block_comparison": [],
            "ngrams_analysis":[],
            "page_structure":[],
            "drmaxs": {}
        }

@pytest.fixture
def mcp_server_module(monkeypatch, tmp_path):
    os.environ["UNIHRA_RESULTS_DIR"] = str(tmp_path / "results")
    project_root = pathlib.Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(project_root / "src"))
    
    import unihra.mcp_server
    return importlib.reload(unihra.mcp_server)

def _tool_result_payload(result):
    return json.loads(result[0].text)

def test_analyze_and_save_workflow(mcp_server_module, tmp_path):
    client = FakeClient(tmp_path / "results")
    server = mcp_server_module.build_server(client)
    
    result = asyncio.run(server._call_tool_handler("unihra_analyze", {
        "own_page": "https://site.com", 
        "competitors":["https://comp.com"]
    }))
    
    payload = _tool_result_payload(result)

    assert "result_id" in payload
    assert payload["own_page"] == "https://site.com"
    assert "data_blocks" in payload

    result_id = payload["result_id"]
    saved_file = tmp_path / "results" / f"{result_id}.json"
    assert saved_file.exists()

def test_read_anchors_segment(mcp_server_module, tmp_path):
    client = FakeClient(tmp_path / "results")
    server = mcp_server_module.build_server(client)

    analyze_res = asyncio.run(server._call_tool_handler("unihra_analyze", {
        "own_page": "https://site.com", "competitors": ["https://comp.com"]
    }))
    
    analyze_payload = _tool_result_payload(analyze_res)
    result_id = analyze_payload["result_id"]

    read_res = asyncio.run(server._call_tool_handler("unihra_get_anchors", {
        "result_id": result_id
    }))
    
    payload = _tool_result_payload(read_res)

    assert "anchors" in payload
    assert len(payload["anchors"]) > 0
    assert payload["anchors"][0]["anchor"] == "купить"