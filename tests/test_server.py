import asyncio

import server


def test_tools_are_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {"search", "retrieve_judgment_text"}


def test_judgment_resource_is_registered():
    templates = asyncio.run(server.mcp.list_resource_templates())
    assert [t.uriTemplate for t in templates] == ["judgment://text/{reference_id}"]


class FakePdfResponse:
    content = b"%PDF-1.4 fake"

    def raise_for_status(self):
        pass


def test_retrieve_judgment_text_writes_nothing_to_stdout(monkeypatch, capsys):
    # stdout is the MCP protocol channel: anything printed there breaks the client.
    monkeypatch.setattr(server.requests, "get", lambda url: FakePdfResponse())
    monkeypatch.setattr(server, "extract_text", lambda path: "texto")

    assert server.retrieve_judgment_text("abc") == "texto"
    assert server.get_judgment_text("abc") == "texto"
    assert capsys.readouterr().out == ""
