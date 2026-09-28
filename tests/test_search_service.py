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
    # The prefix is removed but the space after it is kept.
    assert first["summary"] == " Recurso de casación estimado."

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
