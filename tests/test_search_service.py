from datetime import datetime

import pytest

from services import (
    Comunidad,
    Database,
    Jurisdiccion,
    SearchService,
    SubtipoResolucion,
    TipoOrganoPub,
)
from services import search_service


# Synthetic markup with the same structure poderjudicial.es returns.
RESULTS_HTML = """
<div class="row searchresult doc">
  <div class="title">
    <a href="#">icon</a>
    <a href="/search/AN/openDocument/abc123def456/20240101">STS 1234/2024</a>
  </div>
  <div class="metadatos">
    <ul>
      <li>ROJ: <b>STS 1234/2024</b></li>
      <li>Fecha: <b>15/01/2024</b></li>
    </ul>
  </div>
  <div class="summary">RESUMEN: Recurso de casación estimado.</div>
</div>
<div class="row searchresult doc">
  <div class="title"><a href="/search/AN/openDocument/zzz999/20240102">SAP M 1/2024</a></div>
</div>
"""


def test_format_comunidades():
    values = [Comunidad.MADRID, Comunidad.CATALUNA]
    assert SearchService._format_comunidades(values) == "MADRID(C) | CATALUÑA(C) | "


def test_format_jurisdicciones():
    values = [Jurisdiccion.CIVIL, Jurisdiccion.PENAL]
    assert SearchService._format_jurisdicciones(values) == "|CIVIL||PENAL|"


def test_format_subtipos():
    values = [SubtipoResolucion.SENTENCIA_CASACION, SubtipoResolucion.AUTO_ADMISION]
    assert SearchService._format_subtipos(values) == "SENTENCIA CASACION|AUTO ADMISION"


def test_format_tipo_organo_expands_groups():
    values = [TipoOrganoPub.TRIBUNAL_SUPREMO, TipoOrganoPub.JUZGADO_PENAL]
    assert SearchService._format_tipo_organo(values) == "|11|12|13|14|15|16|51|"


def test_format_tipo_organo_empty():
    assert SearchService._format_tipo_organo([]) == ""


def test_every_tipo_organo_has_a_code():
    assert set(search_service.TIPO_ORGANO_PUB_CODES) == set(TipoOrganoPub)


def test_audiencia_nacional_alias():
    assert Database.AUDIENCIA_NACIONAL is Database.OTROS_TRIBUNALES


def test_extract_reference_id():
    url = "/search/AN/openDocument/abc123def456/20240101"
    assert SearchService.extract_reference_id(url) == "abc123def456"


def test_extract_reference_id_invalid():
    with pytest.raises(ValueError):
        SearchService.extract_reference_id("/search/somethingElse")


def test_parse_results():
    results = SearchService.parse_results(RESULTS_HTML)

    assert len(results) == 2
    first = results[0]
    assert first["title"] == "STS 1234/2024"
    assert first["reference_id"] == "abc123def456"
    assert first["metadata"] == {"ROJ": "STS 1234/2024", "Fecha": "15/01/2024"}
    assert first["summary"] == "Recurso de casación estimado."

    second = results[1]
    assert second["reference_id"] == "zzz999"
    assert second["metadata"] == {}
    assert second["summary"] is None


def test_parse_results_empty_page():
    assert SearchService.parse_results("<html><body></body></html>") == []


class FakeResponse:
    def __init__(self, text=""):
        self.text = text
        self.cookies = self

    def raise_for_status(self):
        pass

    def get_dict(self):
        return {"JSESSIONID": "x"}


def test_fetch_results_builds_payload(monkeypatch):
    sent = {}

    def fake_post(url, data, cookies, headers):
        sent.update(data)
        return FakeResponse(RESULTS_HTML)

    monkeypatch.setattr(search_service.requests, "get", lambda url: FakeResponse())
    monkeypatch.setattr(search_service.requests, "post", fake_post)

    service = SearchService(
        query="despido",
        page=3,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        database=Database.TRIBUNAL_SUPREMO,
        jurisdicciones=[Jurisdiccion.SOCIAL],
        tipo_organo_pub=[TipoOrganoPub.TRIBUNAL_SUPREMO_SOCIAL],
    )
    results = service.fetch_results()

    assert len(results) == 2
    assert sent["TEXT"] == "despido"
    assert sent["start"] == "21"
    assert sent["databasematch"] == "TS"
    assert sent["FECHARESOLUCIONDESDE"] == "01/01/2024"
    assert sent["FECHARESOLUCIONHASTA"] == "31/12/2024"
    assert sent["JURISDICCION"] == "|SOCIAL|"
    assert sent["TIPOORGANOPUB"] == "|14|"
    assert "VALUESCOMUNIDAD" not in sent
    assert "SUBTIPORESOLUCION" not in sent


def test_parse_results_strips_automatic_summary_prefix():
    html = """
    <div class="row searchresult doc">
      <div class="title"><a href="/search/AN/openDocument/r1/x">T</a></div>
      <div class="summary">Resumen Automático: Texto del resumen.</div>
    </div>
    """
    assert SearchService.parse_results(html)[0]["summary"] == "Texto del resumen."


# ---------------------------------------------------------------- sort and case id

from pathlib import Path

from services import CaseHistoryService, SearchServiceError, SortOrder, parse_case_history

RESULT_WITH_CASE = """
<div class="row searchresult doc">
  <div class="title"><a href="/search/AN/openDocument/abc123def456/20240101">STS 1/2024</a></div>
  <a href="#" onclick="showLineaJur('11931977','20261119'); return false;">caso</a>
</div>
"""


def test_parse_results_extracts_case_id():
    results = SearchService.parse_results(RESULT_WITH_CASE + RESULTS_HTML)
    assert results[0]["case_id"] == "11931977"
    assert results[1]["case_id"] is None


def test_sort_is_sent_and_defaults_to_newest(monkeypatch):
    sent = []

    class FakeResponse:
        text = ""

        def raise_for_status(self):
            pass

    monkeypatch.setattr(SearchService, "get_cookies", staticmethod(lambda: {}))
    monkeypatch.setattr(
        search_service.requests,
        "post",
        lambda url, data, cookies, headers: sent.append(data) or FakeResponse(),
    )
    SearchService(query="x").fetch_results()
    SearchService(query="x", sort=SortOrder.RELEVANCIA).fetch_results()
    SearchService(query="x", sort="Relevance").fetch_results()
    assert [d["sort"] for d in sent] == [
        "IN_FECHARESOLUCION:decreasing",
        "Relevance",
        "Relevance",
    ]


# ---------------------------------------------------------------- case history

CASE_HISTORY = (Path(__file__).parent / "fixtures" / "case_history.html").read_text()


def test_parse_case_history():
    history = parse_case_history(CASE_HISTORY)
    rojs = [r.get("roj") for r in history["resolutions"]]
    assert rojs == [None, "SAP S 1105/2023", "ATS 6888/2025", "STS 4483/2026"]
    first = history["resolutions"][0]
    assert first == {"descripcion": "SJPI, Santander, núm. 8, 06-06-2022"}
    ap = history["resolutions"][1]
    assert ap["fecha"] == "2023-07-17"  # epoch ms are midnight Europe/Madrid
    assert ap["fallo"] == "Estima"
    assert ap["id_cendoj"] == "39075370042023100455"
    assert {
        "resolucion": "SAP S 1105/2023",
        "relacion": "recurrida por",
        "por": "STS 4483/2026",
    } in history["relations"]
    # Each edge is listed on both of its nodes upstream; keep it once.
    assert len(history["relations"]) == len(
        {tuple(r.values()) for r in history["relations"]}
    )


def test_case_history_rejects_bad_ids():
    with pytest.raises(SearchServiceError):
        CaseHistoryService("../etc")


def test_accepts_plain_values():
    service = SearchService(
        database="TS",
        jurisdicciones=["CIVIL"],
        comunidades=["MADRID"],
        tipo_organo_pub=["TRIBUNAL_SUPREMO_CIVIL"],
    )
    assert service.database is Database.TRIBUNAL_SUPREMO
    assert service._format_tipo_organo(service.tipo_organo_pub) == "|11|"
