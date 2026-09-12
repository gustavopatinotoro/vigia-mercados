"""
Casos de uso de importación SIPSA.

Coordina adquisición y parsing sin mezclar responsabilidades de dominio,
infraestructura ni análisis científico.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from vigia.dominio.sipsa import (
    RegistroAbastecimiento,
    RegistroPrecioMayorista,
)
from vigia.infraestructura.sipsa import (
    ResultadoDescargaSipsa,
    descargar_xlsx_sipsa,
    parsear_abastecimiento_sipsa,
    parsear_precios_sipsa,
)


@dataclass(frozen=True, slots=True)
class ImportacionSipsa:
    """Resultado de adquisición de una fuente SIPSA."""

    descarga: ResultadoDescargaSipsa


def importar_archivo_precios(
    *,
    url: str,
    destino: Path,
) -> tuple[
    ImportacionSipsa,
    Iterator[RegistroPrecioMayorista],
]:
    """Descarga un boletín de precios y devuelve sus registros canónicos."""
    descarga = descargar_xlsx_sipsa(
        url,
        destino=destino,
    )

    registros = parsear_precios_sipsa(
        descarga.ruta,
        archivo_fuente=descarga.ruta.name,
    )

    return (
        ImportacionSipsa(descarga=descarga),
        registros,
    )


def importar_archivo_abastecimiento(
    *,
    url: str,
    destino: Path,
) -> tuple[
    ImportacionSipsa,
    Iterator[RegistroAbastecimiento],
]:
    """Descarga microdatos de abastecimiento y devuelve sus registros canónicos."""
    descarga = descargar_xlsx_sipsa(
        url,
        destino=destino,
    )

    registros = parsear_abastecimiento_sipsa(
        descarga.ruta,
        archivo_fuente=descarga.ruta.name,
    )

    return (
        ImportacionSipsa(descarga=descarga),
        registros,
    )
