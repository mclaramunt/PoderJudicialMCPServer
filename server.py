
from datetime import datetime
import tempfile
import requests
from pdfminer.high_level import extract_text
from mcp.server.fastmcp import FastMCP

from services import (
    CaseHistoryService,
    Comunidad,
    Database,
    Jurisdiccion,
    SearchService,
    SearchServiceError,
    SortOrder,
    SubtipoResolucion,
    TipoOrganoPub,
)

MIN_TEXT_CHARS = 100
PDF_BY_REFERENCE_URL = (
    "https://www.poderjudicial.es/search/contenidos.action"
    "?action=accessToPDF&reference={}&encode=true"
)
PDF_BY_ID_CENDOJ_URL = (
    "https://www.poderjudicial.es/search/contenidos.action"
    "?action=getdocumentpdf&databasematch=*&idcendoj={}"
)


# Create an MCP server
mcp = FastMCP("Court Judgments API")

# Search endpoint
@mcp.tool()
def search(
    query: str | None = None,
    page: int = 1,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    database: Database = Database.OTROS_TRIBUNALES,
    jurisdicciones: list[Jurisdiccion] | None = None,
    comunidades: list[Comunidad] | None = None,
    subtipos_resolucion: list[SubtipoResolucion] | None = None,
    tipo_organo_pub: list[TipoOrganoPub] | None = None,
    sort: SortOrder = SortOrder.FECHA_DESC,
):
    """Search for Spanish court judgments on poderjudicial.es.

    Args:
        query: Free-text search query (TEXT field).
        page: 1-indexed page number; each page returns up to 10 results.
        start_date: Lower bound for resolution date (FECHARESOLUCIONDESDE).
        end_date: Upper bound for resolution date (FECHARESOLUCIONHASTA).
        database: Which CENDOJ index to search.
            - `TS`: only Tribunal Supremo resolutions.
            - `AN` (default): general CENDOJ index. Despite the legacy "AN"
              code (from `indexAN.jsp`), this is NOT limited to the Audiencia
              Nacional — it covers Tribunal Supremo, Audiencia Nacional,
              Tribunales Superiores de Justicia (TSJ), Audiencias Provinciales
              (AP), juzgados unipersonales y tribunales militares. Use the
              `comunidades` and `tipo_organo_pub` filters to narrow the scope
              (e.g. comunidades=["CATALUÑA"] + tipo_organo_pub=[TSJ_CIVIL_Y_PENAL,
              TSJ_CONTENCIOSO, TSJ_SOCIAL] to target TSJ Cataluña).
        jurisdicciones: Filter by jurisdiction (CIVIL, PENAL, CONTENCIOSO, SOCIAL, MILITAR, ESPECIAL).
        comunidades: Filter by autonomous community (e.g. MADRID, CATALUÑA, ANDALUCÍA).
        subtipos_resolucion: Filter by resolution subtype (e.g. SENTENCIA CASACION, AUTO ADMISION).
        tipo_organo_pub: Filter by organ type (`TipoOrganoPub`). Use specific
            chambers (e.g. `TRIBUNAL_SUPREMO_PENAL`) or umbrella groups that
            expand to every sala (e.g. `TRIBUNAL_SUPREMO`, `AUDIENCIA_NACIONAL`,
            `TRIBUNAL_SUPERIOR_JUSTICIA`).
        sort: Result order. `IN_FECHARESOLUCION:decreasing` (default, newest
            first), `Relevance` (best match for the query first; use it to
            find the leading rulings on a topic), `IN_FECHARESOLUCION:increasing`
            or `IN_FECHAENTRADA:numberdecreasing` (latest added to CENDOJ).

    Each result has a `reference_id` for `retrieve_judgment_text` and, when the
    resolution belongs to a case with several instances, a `case_id` for
    `get_case_history`.
    """
    try:
        search_service = SearchService(
            query=query,
            page=page,
            start_date=start_date,
            end_date=end_date,
            database=database,
            jurisdicciones=jurisdicciones,
            comunidades=comunidades,
            subtipos_resolucion=subtipos_resolucion,
            tipo_organo_pub=tipo_organo_pub,
            sort=sort,
        )
        results = search_service.fetch_results()
        return {"query": query, "results": results}
    except SearchServiceError as e:
        return {"error": str(e)}

def _pdf_text(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp.flush()
            text = extract_text(tmp.name)
        # CENDOJ serves an empty one-page template when the text of a
        # resolution is not available.
        if len(text.strip()) < MIN_TEXT_CHARS:
            return "No text available for this resolution in CENDOJ"
        return text
    except requests.RequestException:
        return "PDF not found"
    except Exception:
        return "Failed to extract text from PDF"


@mcp.tool()
def retrieve_judgment_text(
    reference_id: str | None = None,
    id_cendoj: str | None = None,
):
    """Extract the text of a judgment PDF.

    Args:
        reference_id: `reference_id` from a `search` result.
        id_cendoj: `id_cendoj` of a resolution returned by `get_case_history`
            (use it instead of `reference_id`).
    """
    if id_cendoj:
        if not id_cendoj.isdigit():
            return "Invalid id_cendoj"
        return _pdf_text(PDF_BY_ID_CENDOJ_URL.format(id_cendoj))
    if not reference_id:
        return "Pass reference_id or id_cendoj"
    return _pdf_text(PDF_BY_REFERENCE_URL.format(reference_id))


@mcp.tool()
def get_case_history(case_id: str):
    """Procedural history of a case: every resolution of the same case across
    instances (juzgado, Audiencia Provincial, TSJ, Tribunal Supremo...) and how
    they relate ("recurrida por", "recurso admitido por", "aclarada por").

    Use it to know whether a judgment was appealed, confirmed or reversed. It
    is not a citation graph. Read any of the resolutions with
    `retrieve_judgment_text(id_cendoj=...)`; first-instance judgments not
    published in CENDOJ only have a `descripcion`.

    Args:
        case_id: `case_id` from a `search` result.
    """
    try:
        return CaseHistoryService(case_id).fetch()
    except SearchServiceError as e:
        return {"error": str(e)}


# Get judgment text
@mcp.resource("judgment://text/{reference_id}")
def get_judgment_text(reference_id: str):
    """Extract text from a judgment PDF"""
    return _pdf_text(PDF_BY_REFERENCE_URL.format(reference_id))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
