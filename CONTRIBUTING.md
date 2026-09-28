# Contributing / Cómo contribuir

Thanks for helping! Issues and pull requests are welcome in **English or
Spanish**. / ¡Gracias por ayudar! Puedes abrir issues y pull requests en
**español o inglés**.

## Ways to help

- **Report that the site changed.** This server reads the public search pages
  of poderjudicial.es, so it breaks when the site changes. Use the
  ["poderjudicial.es changed"](https://github.com/mclaramunt/PoderJudicialMCPServer/issues/new?template=site_change.yml)
  template.
- **Report bugs** with the bug report template.
- **Share how you use it**: example prompts, MCP clients you tested, workflows
  for legal research, in
  [Discussions](https://github.com/mclaramunt/PoderJudicialMCPServer/discussions).
- **Send a pull request**: new search filters, better parsing of results or
  PDFs, docs, examples for more MCP clients.

## What is out of scope

The [CGPJ legal notice](https://www.poderjudicial.es/cgpj/es/Poder-Judicial/Tribunal-Supremo/Aviso-legal/)
allows consultation for private use only, and forbids bulk downloading,
commercial use and reuse of the data to build databases without authorisation
(see the notice at the top of the [README](README.md)).

So pull requests that add any of the following **will not be accepted**:

- bulk or automated downloading of judgments (crawlers, "download all pages",
  loops over many PDFs);
- storing, caching or indexing judgments or their text;
- exporting results to build datasets or databases.

Every tool should make **one query per request**: one page of results, or one
PDF. / Cada herramienta debe hacer **una consulta puntual por petición**.

## Development setup

You need Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/mclaramunt/PoderJudicialMCPServer.git
cd PoderJudicialMCPServer
uv sync
uv run pytest
```

To try the server interactively with the
[MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector):

```sh
uv run mcp dev server.py
```

## Where things are

| Path | What it does |
|---|---|
| `server.py` | MCP tools and resources, `main()` entry point |
| `services/search_service.py` | Builds the search request, parses the results page, typed enums for filters |
| `tests/` | Offline tests: they never call poderjudicial.es |

## Guidelines

- **Tests never hit the network.** Use synthetic HTML with the same structure
  as the real page, and `monkeypatch` for `requests` (see
  `tests/test_search_service.py`). Don't commit real judgments or their text.
- **Never write to stdout.** The server talks to the MCP client over stdout;
  use `logging` (stderr) for debug output.
- **Keep enums readable.** New filters should use a readable `Enum` mapped to
  the site's codes, like `TipoOrganoPub`, and be documented in the README.
- One focused change per pull request.

## Pull requests

1. Fork the repo and create a branch from `main`.
2. Make your change with tests, and run `uv run pytest`.
3. Open a pull request describing what changed and why. CI runs the tests on
   Python 3.12 and 3.13.

By contributing you agree that your contributions are licensed under the
[MIT License](LICENSE), and to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
