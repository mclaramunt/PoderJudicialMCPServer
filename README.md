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
| `database` | `Database` | `TS` (only Tribunal Supremo) or `AN` (default; **general CENDOJ index** — despite the legacy code, it covers TS, AN, TSJ, AP, juzgados unipersonales y militares). Use `comunidades` / `tipo_organo_pub` to narrow scope. |
| `jurisdicciones` | `list[Jurisdiccion]` | `CIVIL`, `PENAL`, `CONTENCIOSO`, `SOCIAL`, `MILITAR`, `ESPECIAL`. |
| `comunidades` | `list[Comunidad]` | Autonomous communities (`MADRID`, `CATALUÑA`, `ANDALUCÍA`, …). |
| `subtipos_resolucion` | `list[SubtipoResolucion]` | `SENTENCIA CASACION`, `AUTO ADMISION`, `AUTO INADMISION`, `AUTO OTROS`, `AUTO ACLARATORIO`, `SENTENCIA OTRAS`, `ACUERDO`. |
| `tipo_organo_pub` | `list[TipoOrganoPub]` | Organ-type filter — readable enum (see table below) mapped to the site's numeric codes. |

#### `TipoOrganoPub`

Organ-type enum. Pick specific chambers (e.g. `TRIBUNAL_SUPREMO_PENAL`) or umbrella groups that expand to every sala of that órgano (e.g. `TRIBUNAL_SUPREMO`, `AUDIENCIA_NACIONAL`, `TRIBUNAL_SUPERIOR_JUSTICIA`).

| Enum member | API code | Órgano |
|---|---|---|
| `TRIBUNAL_SUPREMO` | `11\|12\|13\|14\|15\|16` | Tribunal Supremo (todas las salas) |
| `TRIBUNAL_SUPREMO_CIVIL` | `11` | TS · Sala de lo Civil |
| `TRIBUNAL_SUPREMO_PENAL` | `12` | TS · Sala de lo Penal |
| `TRIBUNAL_SUPREMO_CONTENCIOSO` | `13` | TS · Sala de lo Contencioso |
| `TRIBUNAL_SUPREMO_SOCIAL` | `14` | TS · Sala de lo Social |
| `TRIBUNAL_SUPREMO_MILITAR` | `15` | TS · Sala de lo Militar |
| `TRIBUNAL_SUPREMO_ESPECIAL` | `16` | TS · Sala de lo Especial |
| `AUDIENCIA_NACIONAL` | `22\|2264\|23\|24\|25\|26\|27\|28\|29` | Audiencia Nacional (todas las salas y juzgados) |
| `AUDIENCIA_NACIONAL_PENAL` | `22` | AN · Sala de lo Penal |
| `AUDIENCIA_NACIONAL_SALA_APELACION` | `2264` | Sala de Apelación de la AN |
| `AUDIENCIA_NACIONAL_CONTENCIOSO` | `23` | AN · Sala de lo Contencioso |
| `AUDIENCIA_NACIONAL_SOCIAL` | `24` | AN · Sala de lo Social |
| `AUDIENCIA_NACIONAL_JUZGADO_VIGILANCIA_PENITENCIARIA` | `25` | AN · Juzgado Central de Vigilancia Penitenciaria |
| `AUDIENCIA_NACIONAL_JUZGADO_CENTRAL_MENORES` | `26` | AN · Juzgado Central de Menores |
| `AUDIENCIA_NACIONAL_JUZGADOS_CENTRALES_INSTRUCCION` | `27` | AN · Juzgados Centrales de Instrucción |
| `AUDIENCIA_NACIONAL_JUZGADOS_CENTRALES_PENAL` | `28` | AN · Juzgados Centrales de lo Penal |
| `AUDIENCIA_NACIONAL_JUZGADOS_CENTRALES_CONTENCIOSO` | `29` | AN · Juzgados Centrales de lo Contencioso |
| `TRIBUNAL_SUPERIOR_JUSTICIA` | `31\|31201202\|33\|34` | TSJ (todas las salas) |
| `TSJ_CIVIL_Y_PENAL` | `31` | TSJ · Sala de lo Civil y Penal |
| `TSJ_SECCION_APELACION_PENAL` | `31201202` | Sección de Apelación Penal del TSJ |
| `TSJ_CONTENCIOSO` | `33` | TSJ · Sala de lo Contencioso |
| `TSJ_SOCIAL` | `34` | TSJ · Sala de lo Social |
| `AUDIENCIA_PROVINCIAL` | `37` | Audiencia Provincial |
| `AUDIENCIA_PROVINCIAL_TRIBUNAL_JURADO` | `38` | AP · Tribunal del Jurado |
| `AUDIENCIA_TERRITORIAL` | `36` | Audiencia Territorial |
| `TRIBUNAL_MARCA_UE` | `1001` | Tribunal de Marca de la UE |
| `JUZGADOS_MARCA_UE` | `1002` | Juzgados de Marca de la UE |
| `JUZGADO_PRIMERA_INSTANCIA` | `42` | Juzgado de Primera Instancia |
| `JUZGADO_INSTRUCCION` | `43` | Juzgado de Instrucción |
| `JUZGADO_PRIMERA_INSTANCIA_INSTRUCCION` | `41` | Juzgado de 1.ª Inst. e Instrucción |
| `JUZGADO_CONTENCIOSO_ADMINISTRATIVO` | `45` | Juzgado de lo Contencioso-Administrativo |
| `JUZGADO_MENORES` | `53` | Juzgado de Menores |
| `JUZGADO_MERCANTIL` | `47` | Juzgado de lo Mercantil |
| `JUZGADO_PENAL` | `51` | Juzgado de lo Penal |
| `JUZGADO_SOCIAL` | `44` | Juzgado de lo Social |
| `JUZGADO_VIGILANCIA_PENITENCIARIA` | `52` | Juzgado de Vigilancia Penitenciaria |
| `JUZGADO_VIOLENCIA_MUJER` | `48` | Juzgado de Violencia sobre la Mujer |
| `TRIBUNAL_MILITAR_TERRITORIAL` | `83` | Tribunal Militar Territorial |
| `TRIBUNAL_MILITAR_CENTRAL` | `85` | Tribunal Militar Central |
| `CONSEJO_SUPREMO_JUSTICIA_MILITAR` | `75` | Consejo Supremo de Justicia Militar |

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
- `services/` — HTTP/scraping logic and typed enums (`Database`, `Jurisdiccion`, `Comunidad`, `SubtipoResolucion`, `TipoOrganoPub`) for the poderjudicial.es search endpoint.

## License

[MIT](./LICENSE) for the source code. See the `NOTE ON SCOPE` section of the LICENSE file: the MIT grant does not extend to the data served by poderjudicial.es.
