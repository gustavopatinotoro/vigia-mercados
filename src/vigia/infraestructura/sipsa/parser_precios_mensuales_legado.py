"""
Compatibilidad para el esquema histórico SIPSA_P 2013-2018.

La implementación general de los históricos mensuales vive en
``parser_precios_mensuales_historico``. Este módulo conserva la API pública
introducida originalmente para el esquema legado.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from vigia.dominio.sipsa import ObservacionPrecioMensualSipsa
from vigia.infraestructura.sipsa.parser_precios_mensuales_historico import (
    PERFIL_2013_2018,
    ErrorParserPreciosMensualesHistoricoSipsa,
    detectar_perfil_precios_mensuales_sipsa,
    parsear_precios_mensuales_sipsa,
)


class ErrorParserPreciosMensualesLegadoSipsa(RuntimeError):
    """Error producido al interpretar el histórico SIPSA_P 2013-2018."""


def parsear_precios_mensuales_legado_sipsa(
    contenido_csv: bytes,
    *,
    archivo_fuente: str,
) -> Iterator[ObservacionPrecioMensualSipsa]:
    """Interpreta exclusivamente el esquema legado 2013-2018."""
    try:
        perfil = detectar_perfil_precios_mensuales_sipsa(contenido_csv)
    except ErrorParserPreciosMensualesHistoricoSipsa as exc:
        raise ErrorParserPreciosMensualesLegadoSipsa(
            "Encabezado SIPSA_P legado inesperado."
        ) from exc

    if perfil != PERFIL_2013_2018:
        raise ErrorParserPreciosMensualesLegadoSipsa("Encabezado SIPSA_P legado inesperado.")

    try:
        yield from parsear_precios_mensuales_sipsa(
            contenido_csv,
            archivo_fuente=archivo_fuente,
        )
    except ErrorParserPreciosMensualesHistoricoSipsa as exc:
        raise ErrorParserPreciosMensualesLegadoSipsa(str(exc)) from exc


def leer_csv_desde_zip_sipsa(
    ruta_zip: Path,
    *,
    nombre_csv: str,
) -> bytes:
    """Lee de forma segura un CSV específico contenido en un ZIP oficial."""
    if not ruta_zip.exists():
        raise ErrorParserPreciosMensualesLegadoSipsa(f"El archivo ZIP no existe: {ruta_zip}")

    if not ruta_zip.is_file():
        raise ErrorParserPreciosMensualesLegadoSipsa(
            f"La ruta no corresponde a un archivo: {ruta_zip}"
        )

    try:
        with ZipFile(ruta_zip) as archivo_zip:
            if nombre_csv not in archivo_zip.namelist():
                raise ErrorParserPreciosMensualesLegadoSipsa(
                    f"No existe {nombre_csv!r} dentro de {ruta_zip.name}."
                )

            return archivo_zip.read(nombre_csv)

    except BadZipFile as exc:
        raise ErrorParserPreciosMensualesLegadoSipsa(
            f"El archivo no es un ZIP válido: {ruta_zip}"
        ) from exc
