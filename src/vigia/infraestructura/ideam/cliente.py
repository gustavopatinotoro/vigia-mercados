"""
Cliente HTTP para fuentes IDEAM publicadas en Socrata.

Permite realizar consultas filtradas sobre datasets masivos sin descargar
el conjunto completo de datos.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ErrorClienteIdeam(RuntimeError):
    """Error producido durante una consulta al API de IDEAM."""


@dataclass(frozen=True, slots=True)
class ConsultaSocrata:
    """Parámetros soportados para una consulta Socrata."""

    limite: int = 1000
    desplazamiento: int = 0
    filtro: str | None = None
    orden: str | None = None
    seleccion: str | None = None

    def __post_init__(self) -> None:
        if self.limite <= 0:
            raise ValueError("limite debe ser mayor que cero.")

        if self.desplazamiento < 0:
            raise ValueError("desplazamiento no puede ser negativo.")


@dataclass(frozen=True, slots=True)
class PoliticaReintentosIdeam:
    """Configura reintentos frente a fallos transitorios del servicio."""

    maximo_intentos: int = 3
    espera_inicial_segundos: float = 0.5

    def __post_init__(self) -> None:
        if self.maximo_intentos <= 0:
            raise ValueError("maximo_intentos debe ser mayor que cero.")

        if self.espera_inicial_segundos < 0:
            raise ValueError("espera_inicial_segundos no puede ser negativo.")


class ClienteIdeam:
    """Cliente para datasets IDEAM publicados en Datos Abiertos Colombia."""

    BASE_URL = "https://www.datos.gov.co/resource"
    AGENTE_USUARIO = "VIGIA-Mercados/0.1"

    def __init__(
        self,
        *,
        politica_reintentos: PoliticaReintentosIdeam | None = None,
    ) -> None:
        self._politica_reintentos = (
            politica_reintentos if politica_reintentos is not None else PoliticaReintentosIdeam()
        )

    def consultar(
        self,
        dataset_id: str,
        *,
        consulta: ConsultaSocrata | None = None,
        timeout_segundos: float = 30.0,
    ) -> list[dict[str, object]]:
        """
        Ejecuta una consulta JSON contra un dataset Socrata.

        Los fallos transitorios se reintentan de forma limitada. Los errores
        permanentes de la solicitud o los problemas de esquema se propagan
        inmediatamente.
        """
        if not dataset_id.strip():
            raise ValueError("dataset_id no puede estar vacío.")

        if timeout_segundos <= 0:
            raise ValueError("timeout_segundos debe ser mayor que cero.")

        url = self._construir_url(
            dataset_id,
            consulta=consulta,
        )

        solicitud = Request(
            url,
            headers={
                "User-Agent": self.AGENTE_USUARIO,
                "Accept": "application/json",
            },
        )

        contenido, tipo_contenido = self._ejecutar_con_reintentos(
            solicitud,
            timeout_segundos=timeout_segundos,
        )

        if "application/json" not in tipo_contenido:
            raise ErrorClienteIdeam(
                f"IDEAM devolvió un tipo de contenido inesperado: {tipo_contenido!r}"
            )

        try:
            datos = json.loads(contenido)
        except json.JSONDecodeError as exc:
            raise ErrorClienteIdeam("IDEAM devolvió JSON inválido.") from exc

        if not isinstance(datos, list):
            raise ErrorClienteIdeam("La respuesta IDEAM no contiene una lista.")

        registros: list[dict[str, object]] = []

        for registro in datos:
            if not isinstance(registro, dict):
                raise ErrorClienteIdeam("IDEAM devolvió un registro inválido.")

            registros.append(registro)

        return registros

    def _construir_url(
        self,
        dataset_id: str,
        *,
        consulta: ConsultaSocrata | None,
    ) -> str:
        """Construye la URL Socrata sin ejecutar la consulta."""
        parametros: dict[str, str] = {}

        if consulta is not None:
            parametros["$limit"] = str(consulta.limite)
            parametros["$offset"] = str(consulta.desplazamiento)

            if consulta.filtro is not None:
                parametros["$where"] = consulta.filtro

            if consulta.orden is not None:
                parametros["$order"] = consulta.orden

            if consulta.seleccion is not None:
                parametros["$select"] = consulta.seleccion

        url = f"{self.BASE_URL}/{dataset_id}.json"

        if parametros:
            return f"{url}?{urlencode(parametros)}"

        return url

    def _ejecutar_con_reintentos(
        self,
        solicitud: Request,
        *,
        timeout_segundos: float,
    ) -> tuple[bytes, str]:
        """Ejecuta una solicitud con reintentos sólo ante fallos transitorios."""
        ultimo_error: BaseException | None = None

        for intento in range(
            1,
            self._politica_reintentos.maximo_intentos + 1,
        ):
            try:
                return self._ejecutar_solicitud(
                    solicitud,
                    timeout_segundos=timeout_segundos,
                )

            except HTTPError as exc:
                if not self._http_es_transitorio(exc.code):
                    raise ErrorClienteIdeam(
                        f"IDEAM rechazó la solicitud con HTTP {exc.code}."
                    ) from exc

                ultimo_error = exc

            except (
                URLError,
                TimeoutError,
                OSError,
            ) as exc:
                ultimo_error = exc

            if intento < self._politica_reintentos.maximo_intentos:
                espera = self._politica_reintentos.espera_inicial_segundos * intento

                if espera > 0:
                    time.sleep(espera)

        raise ErrorClienteIdeam(
            "No fue posible consultar IDEAM después de "
            f"{self._politica_reintentos.maximo_intentos} intentos: "
            f"{ultimo_error}"
        ) from ultimo_error

    def _ejecutar_solicitud(
        self,
        solicitud: Request,
        *,
        timeout_segundos: float,
    ) -> tuple[bytes, str]:
        """Ejecuta una única solicitud HTTP."""
        with urlopen(
            solicitud,
            timeout=timeout_segundos,
        ) as respuesta:
            if respuesta.status != 200:
                raise ErrorClienteIdeam(f"HTTP inesperado: {respuesta.status}")

            contenido = respuesta.read()

            tipo_contenido = (respuesta.headers.get("Content-Type") or "").lower()

        return contenido, tipo_contenido

    @staticmethod
    def _http_es_transitorio(
        codigo: int,
    ) -> bool:
        """Determina si un estado HTTP admite un reintento seguro."""
        return codigo == 429 or 500 <= codigo <= 599
