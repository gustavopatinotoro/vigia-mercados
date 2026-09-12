"""
Cliente para consultas geoespaciales contra el MGN 2025 de DANE.

Permite resolver una coordenada geográfica WGS84 contra la capa municipal
oficial del Marco Geoestadístico Nacional, sin descargar toda la cartografía.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ErrorClienteMgn(RuntimeError):
    """Error durante una consulta geoespacial al MGN de DANE."""


class ErrorConflictoGeoespacialMgn(RuntimeError):
    """Una coordenada fue asociada con más de un municipio."""


@dataclass(frozen=True, slots=True)
class MunicipioMgn:
    """Municipio identificado por una consulta espacial al MGN."""

    codigo_divipola: str
    departamento: str
    municipio: str

    def __post_init__(self) -> None:
        if len(self.codigo_divipola) != 5:
            raise ValueError("codigo_divipola debe contener exactamente 5 caracteres.")

        if not self.codigo_divipola.isdigit():
            raise ValueError("codigo_divipola debe contener únicamente dígitos.")

        if not self.departamento.strip():
            raise ValueError("departamento no puede estar vacío.")

        if not self.municipio.strip():
            raise ValueError("municipio no puede estar vacío.")


class ClienteMgn:
    """Cliente mínimo para la capa municipal del MGN 2025."""

    URL_CAPA_MUNICIPIO = (
        "https://geoportal.dane.gov.co/mparcgis/rest/services/"
        "Divipola/Serv_DIVIPOLA_MGN_2025/FeatureServer/317/query"
    )

    USER_AGENT = "VIGIA-Mercados/0.1"

    def resolver_punto(
        self,
        *,
        latitud: Decimal,
        longitud: Decimal,
        timeout_segundos: float = 30.0,
    ) -> MunicipioMgn | None:
        """
        Resuelve una coordenada WGS84 mediante intersección con polígonos MGN.

        Retorna None cuando el punto no intersecta ningún municipio.
        """
        self._validar_coordenadas(
            latitud=latitud,
            longitud=longitud,
        )

        if timeout_segundos <= 0:
            raise ValueError("timeout_segundos debe ser mayor que cero.")

        parametros = {
            "f": "json",
            "geometry": f"{longitud},{latitud}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": ("MPIO_CDPMP,MPIO_CNMBRE,DPTO_CNMBRE"),
            "returnGeometry": "false",
        }

        url = f"{self.URL_CAPA_MUNICIPIO}?{urlencode(parametros)}"

        solicitud = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": self.USER_AGENT,
            },
        )

        try:
            with urlopen(
                solicitud,
                timeout=timeout_segundos,
            ) as respuesta:
                contenido = respuesta.read()

        except HTTPError as exc:
            raise ErrorClienteMgn(f"MGN respondió HTTP {exc.code}.") from exc

        except URLError as exc:
            raise ErrorClienteMgn(f"No fue posible consultar MGN: {exc.reason!r}.") from exc

        except TimeoutError as exc:
            raise ErrorClienteMgn("La consulta MGN excedió el tiempo límite.") from exc

        except OSError as exc:
            raise ErrorClienteMgn(f"Error de transporte consultando MGN: {exc}.") from exc

        try:
            datos: object = json.loads(contenido.decode("utf-8"))
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ErrorClienteMgn("MGN devolvió una respuesta JSON inválida.") from exc

        return self._interpretar_respuesta(datos)

    @staticmethod
    def _validar_coordenadas(
        *,
        latitud: Decimal,
        longitud: Decimal,
    ) -> None:
        if not Decimal("-90") <= latitud <= Decimal("90"):
            raise ValueError("latitud fuera del rango [-90, 90].")

        if not Decimal("-180") <= longitud <= Decimal("180"):
            raise ValueError("longitud fuera del rango [-180, 180].")

    @staticmethod
    def _interpretar_respuesta(
        datos: object,
    ) -> MunicipioMgn | None:
        if not isinstance(datos, dict):
            raise ErrorClienteMgn("Respuesta MGN inválida: se esperaba un objeto JSON.")

        if "error" in datos:
            raise ErrorClienteMgn(f"MGN reportó error: {datos['error']!r}.")

        features = datos.get("features")

        if not isinstance(features, list):
            raise ErrorClienteMgn("Respuesta MGN inválida: falta 'features'.")

        if not features:
            return None

        if len(features) > 1:
            raise ErrorConflictoGeoespacialMgn("La coordenada intersecta más de un municipio MGN.")

        feature = features[0]

        if not isinstance(feature, dict):
            raise ErrorClienteMgn("Feature MGN inválido.")

        atributos = feature.get("attributes")

        if not isinstance(atributos, dict):
            raise ErrorClienteMgn("Feature MGN sin atributos válidos.")

        codigo = atributos.get("MPIO_CDPMP")
        departamento = atributos.get("DPTO_CNMBRE")
        municipio = atributos.get("MPIO_CNMBRE")

        if not isinstance(codigo, str):
            raise ErrorClienteMgn("MPIO_CDPMP ausente o inválido.")

        if not isinstance(departamento, str):
            raise ErrorClienteMgn("DPTO_CNMBRE ausente o inválido.")

        if not isinstance(municipio, str):
            raise ErrorClienteMgn("MPIO_CNMBRE ausente o inválido.")

        try:
            return MunicipioMgn(
                codigo_divipola=codigo.strip(),
                departamento=departamento.strip(),
                municipio=municipio.strip(),
            )
        except ValueError as exc:
            raise ErrorClienteMgn(f"Municipio MGN inválido: {exc}") from exc
