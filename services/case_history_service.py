"""History of a case across instances ("Ver resoluciones del Caso" in CENDOJ).

poderjudicial.es links the resolutions of one case (juzgado, Audiencia,
TSJ, Tribunal Supremo...) and the relation between them: appealed by,
appeal admitted by, clarified by... This is the procedural history of one
case, not a citation graph.
"""

import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from .search_service import SearchServiceError

CASE_HISTORY_URL = "https://www.poderjudicial.es/search/jurisprudencia.action"
# The endpoint answers 500 unless the request looks like it comes from the
# search page.
REFERER = "https://www.poderjudicial.es/search/indexAN.jsp"
MADRID = ZoneInfo("Europe/Madrid")

NODE_SPLIT_RE = re.compile(r"type:\s*'nodos'")
ATTRIBUTE_RE = re.compile(r"(\w+):\s*('(?:[^'\\]|\\.)*'|-?\d+|true|false)")
EDGE_RE = re.compile(
    r"nodo:\s*-?\d+,\s*tipoRelacion:\s*'([^']+)',\s*origen:\s*(-?\d+),\s*destino:\s*(-?\d+)"
)
CASE_ID_RE = re.compile(r"^\d{1,12}$")

# tipoRelacion -> readable relation. "*_grafo_por" are the same relations drawn
# across non-adjacent nodes; the site maps "recurrida_adicional_por" likewise.
RELATIONS = {
    "recurrida_por": "recurrida por",
    "recurrida_grafo_por": "recurrida por",
    "recurrida_adicional_por": "recurrida por",
    "admitida_por": "recurso admitido por",
    "admitida_grafo_por": "recurso admitido por",
    "aclarada_por": "aclarada por",
}


def _value(raw: str):
    if raw.startswith("'"):
        return raw[1:-1].replace("\\'", "'").strip()
    if raw in ("true", "false"):
        return raw == "true"
    return int(raw)


def _date(milliseconds) -> str | None:
    if not isinstance(milliseconds, int):
        return None
    moment = datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc)
    return moment.astimezone(MADRID).date().isoformat()


def _relation(kind: str) -> str:
    return RELATIONS.get(kind, kind.replace("_grafo", "").replace("_", " "))


def parse_case_history(text: str) -> dict:
    """Parse the JavaScript object literal the site returns."""
    resolutions: dict[int, dict] = {}
    edges: set[tuple[int, str, int]] = set()
    for chunk in NODE_SPLIT_RE.split(text)[1:]:
        attributes_block = chunk.split("aristas:", 1)[0]
        attributes = {k: _value(v) for k, v in ATTRIBUTE_RE.findall(attributes_block)}
        node_id = attributes.get("idCms")
        if not isinstance(node_id, int):
            continue
        resolution = {
            "roj": re.sub(r"\s+", " ", attributes.get("roj") or "") or None,
            "id_cendoj": attributes.get("idCendoj") or None,
            "organo": attributes.get("organo") or None,
            "tipo": attributes.get("tipo") or None,
            "fecha": _date(attributes.get("fecha")),
            "fallo": attributes.get("fallo") or None,
            # Resolutions not published in CENDOJ (e.g. most first-instance
            # judgments) only carry a description.
            "descripcion": attributes.get("texto") or None,
        }
        resolutions[node_id] = {k: v for k, v in resolution.items() if v}
        for kind, origin, target in EDGE_RE.findall(chunk):
            edges.add((int(origin), _relation(kind), int(target)))

    def label(node_id: int) -> str:
        node = resolutions.get(node_id, {})
        return node.get("roj") or node.get("descripcion") or str(node_id)

    ordered = sorted(resolutions.values(), key=lambda r: r.get("fecha") or "")
    relations = [
        {"resolucion": label(origin), "relacion": kind, "por": label(target)}
        for origin, kind, target in sorted(
            edges, key=lambda e: resolutions.get(e[0], {}).get("fecha") or ""
        )
    ]
    return {"resolutions": ordered, "relations": relations}


class CaseHistoryService:
    def __init__(self, case_id: str):
        if not CASE_ID_RE.match(str(case_id or "")):
            raise SearchServiceError(f"Invalid case_id: {case_id!r}")
        self.case_id = str(case_id)

    def fetch(self) -> dict:
        try:
            response = requests.post(
                CASE_HISTORY_URL,
                data={"action": "getLineaJur", "reference": self.case_id},
                headers={"Referer": REFERER, "X-Requested-With": "XMLHttpRequest"},
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise SearchServiceError(f"Failed to fetch case history: {e}")
        history = parse_case_history(response.text)
        if not history["resolutions"]:
            raise SearchServiceError("No case history for this resolution")
        return history
