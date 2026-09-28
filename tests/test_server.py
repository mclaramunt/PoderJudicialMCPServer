import asyncio

import server


def test_tools_are_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {"search", "retrieve_judgment_text"}


def test_judgment_resource_is_registered():
    templates = asyncio.run(server.mcp.list_resource_templates())
    assert [t.uriTemplate for t in templates] == ["judgment://text/{reference_id}"]
