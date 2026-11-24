import asyncio

import server


def test_tools_are_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {
        "search",
        "retrieve_judgment_text",
        "get_case_history",
    }


def test_judgment_resource_is_registered():
    templates = asyncio.run(server.mcp.list_resource_templates())
    assert [t.uriTemplate for t in templates] == ["judgment://text/{reference_id}"]


LONG_TEXT = "Texto de la sentencia. " * 10


class FakePdfResponse:
    content = b"%PDF-1.4 fake"

    def raise_for_status(self):
        pass


def test_retrieve_judgment_text_writes_nothing_to_stdout(monkeypatch, capsys):
    # stdout is the MCP protocol channel: anything printed there breaks the client.
    monkeypatch.setattr(server.requests, "get", lambda url: FakePdfResponse())
    monkeypatch.setattr(server, "extract_text", lambda path: LONG_TEXT)

    assert server.retrieve_judgment_text("abc") == LONG_TEXT
    assert server.get_judgment_text("abc") == LONG_TEXT
    assert capsys.readouterr().out == ""


def test_retrieve_judgment_text_by_id_cendoj(monkeypatch):
    urls = []

    def fake_get(url):
        urls.append(url)
        return FakePdfResponse()

    monkeypatch.setattr(server.requests, "get", fake_get)
    monkeypatch.setattr(server, "extract_text", lambda path: LONG_TEXT)

    assert server.retrieve_judgment_text(id_cendoj="39075370042023100455") == LONG_TEXT
    assert "action=getdocumentpdf" in urls[0]
    assert "idcendoj=39075370042023100455" in urls[0]
    assert server.retrieve_judgment_text(id_cendoj="../x") == "Invalid id_cendoj"
    assert server.retrieve_judgment_text() == "Pass reference_id or id_cendoj"


def test_search_exposes_sort_values():
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    schema = tools["search"].inputSchema
    assert "Relevance" in schema["$defs"]["SortOrder"]["enum"]


def test_empty_template_pdf_is_reported(monkeypatch):
    monkeypatch.setattr(server.requests, "get", lambda url: FakePdfResponse())
    monkeypatch.setattr(server, "extract_text", lambda path: "JURISPRUDENCIA\n1")
    assert server.retrieve_judgment_text(id_cendoj="1") == (
        "No text available for this resolution in CENDOJ"
    )
