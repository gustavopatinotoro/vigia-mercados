"""
Pruebas unitarias de la descarga reproducible de archivos SIPSA.
"""

from email.message import Message
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import pytest

from vigia.infraestructura.sipsa import (
    ErrorDescargaSipsa,
    descargar_xlsx_sipsa,
)

TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class RespuestaHTTPFalsa:
    """Respuesta HTTP mínima compatible con el descargador."""

    def __init__(
        self,
        contenido: bytes,
        *,
        tipo_contenido: str = TIPO_XLSX,
        estado: int = 200,
    ) -> None:
        self._contenido = contenido
        self._posicion = 0
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

    def read(self, tamanio: int = -1) -> bytes:
        if tamanio < 0:
            resultado = self._contenido[self._posicion :]
            self._posicion = len(self._contenido)
            return resultado

        inicio = self._posicion
        fin = min(
            inicio + tamanio,
            len(self._contenido),
        )
        self._posicion = fin

        return self._contenido[inicio:fin]


def test_descarga_xlsx_valido(tmp_path: Path) -> None:
    """Descarga, persiste y calcula SHA-256 de un XLSX válido."""
    contenido = b"PK\x03\x04" + b"datos-prueba" * 100
    destino = tmp_path / "sipsa.xlsx"

    respuesta = RespuestaHTTPFalsa(contenido)

    with patch(
        "vigia.infraestructura.sipsa.descargador.urlopen",
        return_value=respuesta,
    ):
        resultado = descargar_xlsx_sipsa(
            "https://ejemplo.test/sipsa.xlsx",
            destino=destino,
        )

    assert destino.exists()
    assert destino.read_bytes() == contenido
    assert resultado.ruta == destino
    assert resultado.tamanio_bytes == len(contenido)
    assert resultado.sha256 == sha256(contenido).hexdigest()
    assert resultado.tipo_contenido == TIPO_XLSX


def test_rechaza_tipo_contenido_invalido(
    tmp_path: Path,
) -> None:
    """Rechaza respuestas que no declaran contenido XLSX."""
    destino = tmp_path / "sipsa.xlsx"

    respuesta = RespuestaHTTPFalsa(
        b"PK\x03\x04contenido",
        tipo_contenido="text/html",
    )

    with (
        patch(
            "vigia.infraestructura.sipsa.descargador.urlopen",
            return_value=respuesta,
        ),
        pytest.raises(
            ErrorDescargaSipsa,
            match="Tipo de contenido inesperado",
        ),
    ):
        descargar_xlsx_sipsa(
            "https://ejemplo.test/sipsa.xlsx",
            destino=destino,
        )

    assert not destino.exists()
    assert not destino.with_suffix(".xlsx.parcial").exists()


def test_rechaza_firma_xlsx_invalida(
    tmp_path: Path,
) -> None:
    """Rechaza contenido cuya firma no corresponde a un XLSX."""
    destino = tmp_path / "sipsa.xlsx"

    respuesta = RespuestaHTTPFalsa(
        b"HTML-contenido-invalido",
    )

    with (
        patch(
            "vigia.infraestructura.sipsa.descargador.urlopen",
            return_value=respuesta,
        ),
        pytest.raises(
            ErrorDescargaSipsa,
            match="firma XLSX válida",
        ),
    ):
        descargar_xlsx_sipsa(
            "https://ejemplo.test/sipsa.xlsx",
            destino=destino,
        )

    assert not destino.exists()
    assert not destino.with_suffix(".xlsx.parcial").exists()


def test_elimina_archivo_parcial_ante_error_red(
    tmp_path: Path,
) -> None:
    """No conserva descargas parciales cuando la red falla."""
    destino = tmp_path / "sipsa.xlsx"

    with (
        patch(
            "vigia.infraestructura.sipsa.descargador.urlopen",
            side_effect=URLError("red no disponible"),
        ),
        pytest.raises(
            ErrorDescargaSipsa,
            match="No fue posible descargar SIPSA",
        ),
    ):
        descargar_xlsx_sipsa(
            "https://ejemplo.test/sipsa.xlsx",
            destino=destino,
        )

    assert not destino.exists()
    assert not destino.with_suffix(".xlsx.parcial").exists()
