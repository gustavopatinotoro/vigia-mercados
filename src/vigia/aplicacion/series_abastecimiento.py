"""
Caso de uso para generar la serie diaria agregada de abastecimiento SIPSA_A.

Coordina:

- lectura streaming del XLSX oficial;
- parsing de microdatos;
- agregación diaria por producto, mercado y origen;
- validación de invariantes estructurales;
- persistencia reproducible;
- limpieza de almacenamiento temporal.

Las repeticiones observacionales de la fuente no se deduplican.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vigia.infraestructura.sipsa.agregador_abastecimiento import (
    ErrorAgregacionAbastecimientoSipsa,
    agregar_abastecimiento_diario_sipsa,
    eliminar_base_temporal_abastecimiento,
)
from vigia.infraestructura.sipsa.parser_abastecimiento import (
    ErrorParserAbastecimientoSipsa,
    parsear_abastecimiento_sipsa,
)
from vigia.infraestructura.sipsa.persistencia_abastecimiento import (
    ErrorPersistenciaAbastecimientoSipsa,
    ResultadoPersistenciaAbastecimiento,
    persistir_abastecimiento_diario_sipsa,
)


class ErrorGeneracionAbastecimiento(RuntimeError):
    """Error producido al generar la serie analítica SIPSA_A."""


@dataclass(frozen=True, slots=True)
class ResultadoGeneracionAbastecimiento:
    """Resultado del caso de uso de abastecimiento diario."""

    archivo_fuente: str
    persistencia: ResultadoPersistenciaAbastecimiento


def generar_serie_abastecimiento_sipsa(
    *,
    ruta_fuente: Path,
    directorio_salida: Path,
    ruta_bd_temporal: Path,
    nombre: str = "abastecimiento_diario_2026",
) -> ResultadoGeneracionAbastecimiento:
    """
    Genera y persiste la serie diaria agregada de abastecimiento SIPSA_A.

    La granularidad resultante es:

    ``fecha + producto + mercado + departamento_origen + municipio_origen``.

    ``cantidad_kg`` corresponde a la suma exacta de todas las observaciones
    fuente pertenecientes a cada clave analítica.
    """
    if not ruta_fuente.exists():
        raise ErrorGeneracionAbastecimiento(f"No existe la fuente SIPSA_A: {ruta_fuente}")

    if not ruta_fuente.is_file():
        raise ErrorGeneracionAbastecimiento(f"La fuente SIPSA_A no es un archivo: {ruta_fuente}")

    if ruta_fuente.resolve() == ruta_bd_temporal.resolve():
        raise ErrorGeneracionAbastecimiento(
            "La base temporal no puede utilizar la misma ruta que la fuente."
        )

    registros = parsear_abastecimiento_sipsa(
        ruta_fuente,
        archivo_fuente=ruta_fuente.name,
    )

    observaciones = agregar_abastecimiento_diario_sipsa(
        registros,
        ruta_bd_temporal=ruta_bd_temporal,
        confirmar_cada=10_000,
    )

    try:
        persistencia = persistir_abastecimiento_diario_sipsa(
            observaciones,
            directorio=directorio_salida,
            nombre=nombre,
        )

    except (
        ErrorParserAbastecimientoSipsa,
        ErrorAgregacionAbastecimientoSipsa,
        ErrorPersistenciaAbastecimientoSipsa,
        ValueError,
    ) as exc:
        raise ErrorGeneracionAbastecimiento(
            f"No fue posible generar la serie SIPSA_A: {exc}"
        ) from exc

    finally:
        try:
            eliminar_base_temporal_abastecimiento(ruta_bd_temporal)
        except ErrorAgregacionAbastecimientoSipsa as exc:
            raise ErrorGeneracionAbastecimiento(
                f"La serie fue procesada, pero falló la limpieza de la base temporal: {exc}"
            ) from exc

    return ResultadoGeneracionAbastecimiento(
        archivo_fuente=ruta_fuente.name,
        persistencia=persistencia,
    )
