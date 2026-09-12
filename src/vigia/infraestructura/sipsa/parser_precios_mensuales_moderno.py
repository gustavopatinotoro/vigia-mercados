"""
Compatibilidad para el esquema mensual SIPSA_P observado en 2024.

La implementación general vive en ``parser_precios_mensuales_historico``.
Este módulo conserva la API pública introducida originalmente para el
esquema moderno con código CPC.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from vigia.dominio.sipsa import ObservacionPrecioMensualSipsa
from vigia.infraestructura.sipsa.parser_precios_mensuales_historico import (
    PERFIL_2024,
    ErrorParserPreciosMensualesHistoricoSipsa,
    detectar_perfil_precios_mensuales_sipsa,
    parsear_precios_mensuales_sipsa,
)


class ErrorParserPreciosMensualesModernoSipsa(RuntimeError):
    """Error producido al interpretar el esquema SIPSA_P 2024."""


def parsear_precios_mensuales_moderno_sipsa(
    contenido_csv: bytes,
    *,
    archivo_fuente: str,
) -> Iterator[ObservacionPrecioMensualSipsa]:
    """Interpreta exclusivamente el esquema moderno 2024."""
    try:
        perfil = detectar_perfil_precios_mensuales_sipsa(contenido_csv)
    except ErrorParserPreciosMensualesHistoricoSipsa as exc:
        raise ErrorParserPreciosMensualesModernoSipsa(
            "Encabezado SIPSA_P moderno inesperado."
        ) from exc

    if perfil != PERFIL_2024:
        raise ErrorParserPreciosMensualesModernoSipsa("Encabezado SIPSA_P moderno inesperado.")

    try:
        yield from parsear_precios_mensuales_sipsa(
            contenido_csv,
            archivo_fuente=archivo_fuente,
        )
    except ErrorParserPreciosMensualesHistoricoSipsa as exc:
        raise ErrorParserPreciosMensualesModernoSipsa(str(exc)) from exc


def leer_csv_desde_zip_sipsa_moderno(
    ruta_zip: Path,
    *,
    nombre_csv: str,
) -> bytes:
    """Lee un CSV moderno específico contenido en un ZIP oficial."""
    if not ruta_zip.exists():
        raise ErrorParserPreciosMensualesModernoSipsa(f"El archivo ZIP no existe: {ruta_zip}")

    if not ruta_zip.is_file():
        raise ErrorParserPreciosMensualesModernoSipsa(
            f"La ruta no corresponde a un archivo: {ruta_zip}"
        )

    try:
        with ZipFile(ruta_zip) as archivo_zip:
            if nombre_csv not in archivo_zip.namelist():
                raise ErrorParserPreciosMensualesModernoSipsa(
                    f"No existe {nombre_csv!r} dentro de {ruta_zip.name}."
                )

            return archivo_zip.read(nombre_csv)

    except BadZipFile as exc:
        raise ErrorParserPreciosMensualesModernoSipsa(
            f"El archivo no es un ZIP válido: {ruta_zip}"
        ) from exc
