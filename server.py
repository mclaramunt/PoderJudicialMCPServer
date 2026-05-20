
from datetime import datetime
import tempfile
import requests
from pdfminer.high_level import extract_text
from mcp.server.fastmcp import FastMCP

from services import (
    Comunidad,
    Database,
    Jurisdiccion,
    SearchService,
    SearchServiceError,
    SubtipoResolucion,
    TipoOrganoPub,
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
        )
        results = search_service.fetch_results()
        return {"query": query, "results": results}
    except SearchServiceError as e:
        return {"error": str(e)}

# Search endpoint
@mcp.tool()
def retrieve_judgment_text(
    reference_id: str
):
    """Extract text from a judgment PDF"""
    url = (
        "https://www.poderjudicial.es/search/contenidos.action"
        "?action=accessToPDF"
        f"&reference={reference_id}"
        "&encode=true"
    )
    try:
        response = requests.get(url)
        print(response)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp.flush()
            text = extract_text(tmp.name)
        return text
    except requests.RequestException:
        return "PDF not found"
    except Exception:
        return "Failed to extract text from PDF"


# Get judgment text
@mcp.resource("judgment://text/{reference_id}")
def get_judgment_text(reference_id: str):
    """Extract text from a judgment PDF"""
    url = (
        "https://www.poderjudicial.es/search/contenidos.action"
        "?action=accessToPDF"
        f"&reference={reference_id}"
        "&encode=true"
    )
    try:
        response = requests.get(url)
        print(response)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp.flush()
            text = extract_text(tmp.name)
        return text
    except requests.RequestException:
        return "PDF not found"
    except Exception:
        return "Failed to extract text from PDF"


def main():
    mcp.run()


if __name__ == "__main__":
    main()
