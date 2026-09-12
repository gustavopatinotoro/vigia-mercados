"""
Pruebas unitarias del cliente Socrata IDEAM.
"""

from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from vigia.infraestructura.ideam.cliente import (
    ClienteIdeam,
    ConsultaSocrata,
    ErrorClienteIdeam,
    PoliticaReintentosIdeam,
)


class RespuestaHTTPFalsa:
    """Respuesta HTTP mínima para pruebas."""

    def __init__(
        self,
        contenido: bytes,
        *,
        tipo_contenido: str = "application/json",
        estado: int = 200,
    ) -> None:
        self._contenido = contenido
        self.status = estado

        cabeceras = Message()
        cabeceras["Content-Type"] = tipo_contenido
        self.headers = cabeceras

    def __enter__(self) -> RespuestaHTTPFalsa:
        return self

    def __exit__(
        self,
        tipo: object,
        valor: object,
        traza: object,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self._contenido


def _cliente_sin_espera(
    *,
    maximo_intentos: int = 3,
) -> ClienteIdeam:
    """Construye un cliente rápido para pruebas de reintentos."""
    return ClienteIdeam(
        politica_reintentos=PoliticaReintentosIdeam(
            maximo_intentos=maximo_intentos,
            espera_inicial_segundos=0,
        )
    )


def _cabeceras_http() -> Message[str, str]:
    """Construye cabeceras válidas para errores HTTP simulados."""
    return Message()


def test_consulta_json_valido() -> None:
    """Devuelve registros válidos desde Socrata."""
    respuesta = RespuestaHTTPFalsa(b'[{"codigo":"001","nombre":"ESTACION"}]')

    cliente = _cliente_sin_espera()

    with patch(
        "vigia.infraestructura.ideam.cliente.urlopen",
        return_value=respuesta,
    ):
        registros = cliente.consultar(
            "dataset",
            consulta=ConsultaSocrata(limite=10),
        )

    assert len(registros) == 1
    assert registros[0]["codigo"] == "001"


def test_rechaza_limite_invalido() -> None:
    """Impide consultas con límite no positivo."""
    with pytest.raises(
        ValueError,
        match="limite debe ser mayor que cero",
    ):
        ConsultaSocrata(limite=0)


def test_rechaza_desplazamiento_negativo() -> None:
    """Impide desplazamientos negativos."""
    with pytest.raises(
        ValueError,
        match="desplazamiento no puede ser negativo",
    ):
        ConsultaSocrata(desplazamiento=-1)


def test_rechaza_dataset_vacio() -> None:
    """Impide consultas sin identificador."""
    cliente = _cliente_sin_espera()

    with pytest.raises(
        ValueError,
        match="dataset_id no puede estar vacío",
    ):
        cliente.consultar("   ")


def test_rechaza_timeout_no_positivo() -> None:
    """Impide configurar un timeout inválido."""
    cliente = _cliente_sin_espera()

    with pytest.raises(
        ValueError,
        match="timeout_segundos debe ser mayor que cero",
    ):
        cliente.consultar(
            "dataset",
            timeout_segundos=0,
        )


def test_rechaza_politica_sin_intentos() -> None:
    """La política debe permitir al menos un intento."""
    with pytest.raises(
        ValueError,
        match="maximo_intentos debe ser mayor que cero",
    ):
        PoliticaReintentosIdeam(maximo_intentos=0)


def test_rechaza_espera_negativa() -> None:
    """La espera inicial nunca puede ser negativa."""
    with pytest.raises(
        ValueError,
        match="espera_inicial_segundos no puede ser negativo",
    ):
        PoliticaReintentosIdeam(espera_inicial_segundos=-1)


def test_rechaza_tipo_contenido_invalido() -> None:
    """Rechaza respuestas que no sean JSON."""
    respuesta = RespuestaHTTPFalsa(
        b"<html></html>",
        tipo_contenido="text/html",
    )

    cliente = _cliente_sin_espera()

    with (
        patch(
            "vigia.infraestructura.ideam.cliente.urlopen",
            return_value=respuesta,
        ),
        pytest.raises(
            ErrorClienteIdeam,
            match="tipo de contenido inesperado",
        ),
    ):
        cliente.consultar("dataset")


def test_rechaza_json_invalido() -> None:
    """Rechaza una respuesta JSON corrupta."""
    respuesta = RespuestaHTTPFalsa(b"{json-invalido}")

    cliente = _cliente_sin_espera()

    with (
        patch(
            "vigia.infraestructura.ideam.cliente.urlopen",
            return_value=respuesta,
        ),
        pytest.raises(
            ErrorClienteIdeam,
            match="JSON inválido",
        ),
    ):
        cliente.consultar("dataset")


def test_reintenta_timeout_y_se_recupera() -> None:
    """Un timeout transitorio no aborta inmediatamente la consulta."""
    respuesta = RespuestaHTTPFalsa(b'[{"codigo":"001"}]')

    cliente = _cliente_sin_espera()

    with patch(
        "vigia.infraestructura.ideam.cliente.urlopen",
        side_effect=[
            TimeoutError("timeout temporal"),
            respuesta,
        ],
    ) as abrir:
        registros = cliente.consultar("dataset")

    assert registros == [{"codigo": "001"}]
    assert abrir.call_count == 2


def test_agota_reintentos_ante_timeout() -> None:
    """Falla de forma explícita cuando todos los intentos expiran."""
    cliente = _cliente_sin_espera(maximo_intentos=3)

    with (
        patch(
            "vigia.infraestructura.ideam.cliente.urlopen",
            side_effect=TimeoutError("timeout persistente"),
        ) as abrir,
        pytest.raises(
            ErrorClienteIdeam,
            match="después de 3 intentos",
        ),
    ):
        cliente.consultar("dataset")

    assert abrir.call_count == 3


def test_reintenta_http_500_y_se_recupera() -> None:
    """Los errores HTTP del servidor son considerados transitorios."""
    error = HTTPError(
        url="https://ejemplo.test",
        code=500,
        msg="Internal Server Error",
        hdrs=_cabeceras_http(),
        fp=None,
    )

    respuesta = RespuestaHTTPFalsa(b'[{"codigo":"001"}]')

    cliente = _cliente_sin_espera()

    with patch(
        "vigia.infraestructura.ideam.cliente.urlopen",
        side_effect=[
            error,
            respuesta,
        ],
    ) as abrir:
        registros = cliente.consultar("dataset")

    assert registros == [{"codigo": "001"}]
    assert abrir.call_count == 2


def test_no_reintenta_http_400() -> None:
    """Los errores permanentes de la solicitud no deben reintentarse."""
    error = HTTPError(
        url="https://ejemplo.test",
        code=400,
        msg="Bad Request",
        hdrs=_cabeceras_http(),
        fp=None,
    )

    cliente = _cliente_sin_espera()

    with (
        patch(
            "vigia.infraestructura.ideam.cliente.urlopen",
            side_effect=error,
        ) as abrir,
        pytest.raises(
            ErrorClienteIdeam,
            match="HTTP 400",
        ),
    ):
        cliente.consultar("dataset")

    assert abrir.call_count == 1
