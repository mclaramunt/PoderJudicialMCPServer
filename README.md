# Poder Judicial MCP Server

An MCP (Model Context Protocol) server that exposes search and retrieval of Spanish court judgments from [poderjudicial.es](https://www.poderjudicial.es).

> ⚠️ **Aviso legal — léelo antes de usar este software**
>
> Las resoluciones expuestas por este servidor son propiedad del [CGPJ](https://www.poderjudicial.es) y están sujetas al [aviso legal de poderjudicial.es](https://www.poderjudicial.es/cgpj/es/Poder-Judicial/Tribunal-Supremo/Aviso-legal/). En particular, en el momento de escribir esto, dicho aviso:
>
> - permite la consulta **solo para uso particular**;
> - **prohíbe el uso comercial**;
> - **prohíbe la descarga masiva** de información;
> - **prohíbe la reutilización para crear bases de datos** o con fines comerciales sin autorización expresa del Centro de Documentación Judicial del CGPJ.
>
> Este repositorio publica únicamente el **código** de un cliente MCP que realiza consultas en vivo a poderjudicial.es. **No indexa, almacena ni redistribuye sentencias.** La licencia MIT cubre el código, no los datos.
>
> El cumplimiento del aviso legal del CGPJ es **responsabilidad exclusiva del usuario final** del software. Por diseño, este servidor expone únicamente operaciones de consulta puntual (una página de resultados o un PDF concreto por petición) y no incluye utilidades de descarga masiva.

## Tools

### `search(...)`

Search court judgments. Returns a paginated list with titles, metadata, summaries and a `reference_id` for each result.

| Parameter | Type | Description |
|---|---|---|
| `query` | `str \| None` | Free-text search (`TEXT` field). |
| `page` | `int` | 1-indexed page; 10 results per page. |
| `start_date` / `end_date` | `datetime \| None` | Resolution-date bounds. |
| `database` | `Database` | `TS` (Tribunal Supremo) or `AN` (Audiencia Nacional, default). |
| `jurisdicciones` | `list[Jurisdiccion]` | `CIVIL`, `PENAL`, `CONTENCIOSO`, `SOCIAL`, `MILITAR`, `ESPECIAL`. |
| `comunidades` | `list[Comunidad]` | Autonomous communities (`MADRID`, `CATALUÑA`, `ANDALUCÍA`, …). |
| `subtipos_resolucion` | `list[SubtipoResolucion]` | `SENTENCIA CASACION`, `AUTO ADMISION`, `AUTO INADMISION`, `AUTO OTROS`, `AUTO ACLARATORIO`, `SENTENCIA OTRAS`, `ACUERDO`. |
| `tipo_organo_pub` | `list[str]` | Opaque numeric organ-type codes (e.g. `["11", "12", "2264"]`). |

### `retrieve_judgment_text(reference_id)`

Download the judgment PDF for a given `reference_id` and return its extracted text.

## Resources

- **`judgment://text/{reference_id}`** — Same as `retrieve_judgment_text`, exposed as an MCP resource.

## Run via `pipx` (recommended)

No clone required. Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "poder-judicial-mcp": {
      "command": "pipx",
      "args": [
        "run",
        "--spec",
        "git+https://github.com/mclaramunt/PoderJudicialMCPServer.git",
        "poder-judicial-mcp"
      ]
    }
  }
}
```

`pipx` will fetch the repo, build the package in an isolated environment, and launch the server.

Requirements on the host: Python ≥ 3.12 and [`pipx`](https://pipx.pypa.io/) installed.

## Run from a local checkout

Using [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync
uv run poder-judicial-mcp
```

Or with plain `pip`:

```bash
pip install -e .
poder-judicial-mcp
```

## Development

Project layout:

- `server.py` — FastMCP server, tool and resource definitions, `main()` entry point.
- `services/` — HTTP/scraping logic and typed enums (`Database`, `Jurisdiccion`, `Comunidad`, `SubtipoResolucion`) for the poderjudicial.es search endpoint.

## License

[MIT](./LICENSE) for the source code. See the `NOTE ON SCOPE` section of the LICENSE file: the MIT grant does not extend to the data served by poderjudicial.es.
