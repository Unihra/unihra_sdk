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
        self._list_tools_handler = None
    def list_tools(self):
        def decorator(func): self._list_tools_handler = func; return func
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
    """Records the kwargs analyze() was called with so tests can assert the model's choices."""

    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.last_kwargs = None

    def analyze(self, **kwargs):
        self.last_kwargs = kwargs
        base = {
            "anchors_analysis": [
                {
                    "anchor": "купить",
                    "frequency_own": 0,
                    "frequency_comp_avg": 5.0,
                    "pages_count": 3,
                    "links": ["https://comp1.com/buy", "https://comp2.com/shop"],
                }
            ],
            "semantic_context_analysis": [],
            "block_comparison": [],
            "ngrams_analysis": [],
            "page_structure": [],
        }
        if kwargs.get("triplet_analysis"):
            base["triplets_analysis"] = {
                "entities": [
                    {
                        "subject": "Минеральная вата",
                        "tier": "core",
                        "triplets_count": 2,
                        "sources_count": 3,
                        "triplets": [
                            {"predicate": "не горит", "object": "да",
                             "sources": ["c1.com", "c2.com", "c3.com"]}
                        ],
                    }
                ],
                "gaps": {
                    "critical":  [{"subject": "Сертификат пожарной безопасности"}],
                    "important": [],
                    "unique":    [],
                },
                "stats": {
                    "total_triplets": 2,
                    "sources_with_content": 3,
                    "gaps_critical": 1,
                    "gaps_important": 0,
                    "gaps_unique": 0,
                    "gaps_total": 1,
                },
            }
        return base


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
        "competitors": ["https://comp.com"],
    }))

    payload = _tool_result_payload(result)

    assert "result_id" in payload
    assert payload["own_page"] == "https://site.com"
    assert payload["triplet_analysis"] is False
    assert payload["credits_spent"] == 1
    assert "data_blocks" in payload
    # No triplets in standard mode
    assert "triplets_summary" not in payload

    # Standard analysis should NOT request triplets server-side
    assert client.last_kwargs["triplet_analysis"] is False

    result_id = payload["result_id"]
    saved_file = tmp_path / "results" / f"{result_id}.json"
    assert saved_file.exists()


def test_analyze_with_triplets_flag_propagates(mcp_server_module, tmp_path):
    """When the model passes triplet_analysis=true, the SDK call must mirror it
    and the summary must include the triplets headline numbers."""
    client = FakeClient(tmp_path / "results")
    server = mcp_server_module.build_server(client)

    result = asyncio.run(server._call_tool_handler("unihra_analyze", {
        "own_page": "https://site.com",
        "competitors": ["https://comp.com"],
        "triplet_analysis": True,
    }))

    payload = _tool_result_payload(result)

    assert client.last_kwargs["triplet_analysis"] is True
    assert payload["triplet_analysis"] is True
    assert payload["credits_spent"] == 5
    assert payload["data_blocks"]["triplets_entities"] == 1
    assert payload["data_blocks"]["triplets_gaps_total"] == 1
    assert payload["triplets_summary"]["gaps_critical"] == 1
    assert payload["triplets_summary"]["entities_by_tier"] == {"core": 1}


def test_read_anchors_segment(mcp_server_module, tmp_path):
    client = FakeClient(tmp_path / "results")
    server = mcp_server_module.build_server(client)

    analyze_res = asyncio.run(server._call_tool_handler("unihra_analyze", {
        "own_page": "https://site.com", "competitors": ["https://comp.com"],
    }))

    analyze_payload = _tool_result_payload(analyze_res)
    result_id = analyze_payload["result_id"]

    read_res = asyncio.run(server._call_tool_handler("unihra_get_anchors", {
        "result_id": result_id,
    }))

    payload = _tool_result_payload(read_res)

    assert "anchors" in payload
    assert len(payload["anchors"]) > 0
    assert payload["anchors"][0]["anchor"] == "купить"

    # Verify links field is present and contains expected values
    assert "links" in payload["anchors"][0]
    assert payload["anchors"][0]["links"] == ["https://comp1.com/buy", "https://comp2.com/shop"]


def test_get_triplets_returns_entities_and_gaps(mcp_server_module, tmp_path):
    """unihra_get_triplets must return both views by default and respect tier filters."""
    client = FakeClient(tmp_path / "results")
    server = mcp_server_module.build_server(client)

    analyze_res = asyncio.run(server._call_tool_handler("unihra_analyze", {
        "own_page": "https://site.com",
        "competitors": ["https://comp.com"],
        "triplet_analysis": True,
    }))
    result_id = _tool_result_payload(analyze_res)["result_id"]

    triplets_res = asyncio.run(server._call_tool_handler("unihra_get_triplets", {
        "result_id": result_id,
    }))
    payload = _tool_result_payload(triplets_res)

    assert payload["view"] == "both"
    # entities (core tier is in default filter)
    assert len(payload["entities"]) == 1
    assert payload["entities"][0]["subject"] == "Минеральная вата"
    # default gap_severities = critical + important
    assert "critical" in payload["gaps"]
    assert payload["gaps"]["critical"][0]["subject"] == "Сертификат пожарной безопасности"
    assert payload["stats"]["gaps_total"] == 1


def test_get_triplets_errors_on_standard_result(mcp_server_module, tmp_path):
    """Calling unihra_get_triplets on a standard-mode result must explain the limitation."""
    client = FakeClient(tmp_path / "results")
    server = mcp_server_module.build_server(client)

    analyze_res = asyncio.run(server._call_tool_handler("unihra_analyze", {
        "own_page": "https://site.com",
        "competitors": ["https://comp.com"],
        # triplet_analysis defaults to false
    }))
    result_id = _tool_result_payload(analyze_res)["result_id"]

    triplets_res = asyncio.run(server._call_tool_handler("unihra_get_triplets", {
        "result_id": result_id,
    }))
    payload = _tool_result_payload(triplets_res)
    assert "error" in payload
    assert "triplet_analysis=true" in payload["error"]
