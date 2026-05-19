import re
from datetime import datetime
from enum import Enum

import requests
from bs4 import BeautifulSoup


class SearchServiceError(Exception):
    """Custom exception for SearchService errors."""
    pass


class Database(str, Enum):
    TRIBUNAL_SUPREMO = "TS"
    AUDIENCIA_NACIONAL = "AN"


class Jurisdiccion(str, Enum):
    CIVIL = "CIVIL"
    PENAL = "PENAL"
    CONTENCIOSO = "CONTENCIOSO"
    SOCIAL = "SOCIAL"
    MILITAR = "MILITAR"
    ESPECIAL = "ESPECIAL"


class Comunidad(str, Enum):
    ANDALUCIA = "ANDALUCÍA"
    ARAGON = "ARAGÓN"
    ASTURIAS = "ASTURIAS"
    BALEARES = "BALEARES"
    CANARIAS = "CANARIAS"
    CANTABRIA = "CANTABRIA"
    CASTILLA_LA_MANCHA = "CASTILLA LA MANCHA"
    CASTILLA_Y_LEON = "CASTILLA Y LEÓN"
    CATALUNA = "CATALUÑA"
    CEUTA = "CEUTA"
    COMUNIDAD_VALENCIANA = "COMUNIDAD VALENCIANA"
    EXTREMADURA = "EXTREMADURA"
    GALICIA = "GALICIA"
    LA_RIOJA = "LA RIOJA"
    PAIS_VASCO = "PAÍS VASCO"
    NAVARRA = "NAVARRA"
    MURCIA = "MURCIA"
    MELILLA = "MELILLA"
    MADRID = "MADRID"


class SubtipoResolucion(str, Enum):
    AUTO_ACLARATORIO = "AUTO ACLARATORIO"
    AUTO_ADMISION = "AUTO ADMISION"
    AUTO_INADMISION = "AUTO INADMISION"
    AUTO_OTROS = "AUTO OTROS"
    SENTENCIA_CASACION = "SENTENCIA CASACION"
    SENTENCIA_OTRAS = "SENTENCIA OTRAS"
    ACUERDO = "ACUERDO"


class SearchService:
    SEARCH_URL = "https://www.poderjudicial.es/search/search.action"
    RECORDS_PER_PAGE = 10

    def __init__(
        self,
        query: str | None = None,
        page: int = 1,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        database: Database = Database.AUDIENCIA_NACIONAL,
        jurisdicciones: list[Jurisdiccion] | None = None,
        comunidades: list[Comunidad] | None = None,
        subtipos_resolucion: list[SubtipoResolucion] | None = None,
        tipo_organo_pub: list[str] | None = None,
    ):
        self.query = query
        self.page = page
        self.start_date = start_date
        self.end_date = end_date
        self.database = database
        self.jurisdicciones = jurisdicciones or []
        self.comunidades = comunidades or []
        self.subtipos_resolucion = subtipos_resolucion or []
        self.tipo_organo_pub = tipo_organo_pub or []

    @staticmethod
    def get_cookies():
        try:
            response = requests.get('https://www.poderjudicial.es/search/indexAN.jsp')
            response.raise_for_status()
            return response.cookies.get_dict()
        except requests.RequestException as e:
            raise SearchServiceError(f"Failed to fetch cookies: {e}")

    @staticmethod
    def _format_comunidades(values: list[Comunidad]) -> str:
        # Site format: "NAME(C) | NAME(C) | ... | NAME(C) | "
        return "".join(f"{v.value}(C) | " for v in values)

    @staticmethod
    def _format_jurisdicciones(values: list[Jurisdiccion]) -> str:
        # Site format: "|VAL||VAL||VAL|"
        return "".join(f"|{v.value}|" for v in values)

    @staticmethod
    def _format_subtipos(values: list[SubtipoResolucion]) -> str:
        # Site format: "VAL|VAL|VAL"
        return "|".join(v.value for v in values)

    @staticmethod
    def _format_tipo_organo(values: list[str]) -> str:
        # Site format: "|CODE|CODE|...|" — codes are opaque numeric identifiers
        if not values:
            return ""
        return "|" + "|".join(values) + "|"

    def fetch_results(self):
        start = (self.page - 1) * SearchService.RECORDS_PER_PAGE + 1
        payload = {
            "action": "query",
            "sort": "IN_FECHARESOLUCION:decreasing",
            "recordsPerPage": str(SearchService.RECORDS_PER_PAGE),
            "databasematch": self.database.value,
            "start": str(start),
            "TEXT": self.query or "",
            "FECHARESOLUCIONDESDE": self.start_date.strftime("%d/%m/%Y") if self.start_date else "",
            "FECHARESOLUCIONHASTA": self.end_date.strftime("%d/%m/%Y") if self.end_date else "",
        }
        if self.comunidades:
            payload["VALUESCOMUNIDAD"] = self._format_comunidades(self.comunidades)
        if self.jurisdicciones:
            payload["JURISDICCION"] = self._format_jurisdicciones(self.jurisdicciones)
        if self.subtipos_resolucion:
            payload["SUBTIPORESOLUCION"] = self._format_subtipos(self.subtipos_resolucion)
        if self.tipo_organo_pub:
            payload["TIPOORGANOPUB"] = self._format_tipo_organo(self.tipo_organo_pub)

        cookies = SearchService.get_cookies()
        headers = {"Referer": "https://www.poderjudicial.es/search/indexAN.jsp"}

        try:
            response = requests.post(SearchService.SEARCH_URL, data=payload, cookies=cookies, headers=headers)
            response.raise_for_status()
            return self.parse_results(response.text)
        except requests.RequestException as e:
            raise SearchServiceError(f"Failed to fetch search results: {e}")

    @staticmethod
    def parse_results(html: str):
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for item in soup.select("div.row.searchresult.doc"):
            title_tag = item.select("div.title a")[-1] if item.select("div.title a") else None
            title = title_tag.get_text(strip=True) if title_tag else None
            link = title_tag["href"] if title_tag and title_tag.has_attr("href") else None
            reference_id = SearchService.extract_reference_id(link) if link else None
            metadata = {}
            for li in item.select("div.metadatos ul li"):
                key = li.get_text(strip=True).split(":")[0]
                value = li.find("b").get_text(strip=True) if li.find("b") else None
                metadata[key] = value

            summary = item.select_one("div.summary").get_text(strip=True).replace("RESUMEN:", "").replace("Resumen Automático:", "") if item.select_one("div.summary") else None

            results.append({
                "title": title,
                "link": link,
                "metadata": metadata,
                "summary": summary,
                "reference_id": reference_id
            })

        return results

    @staticmethod
    def extract_reference_id(reference_url: str) -> str:
        # Extracts the reference_id from the URL
        match = re.search(r'/openDocument/([^/]+)/', reference_url)
        if match:
            return match.group(1)
        raise ValueError("Invalid reference URL format")
