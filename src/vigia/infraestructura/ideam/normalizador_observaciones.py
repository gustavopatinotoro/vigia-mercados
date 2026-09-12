"""
Normalización de observaciones climáticas IDEAM.

Elimina exclusivamente duplicados exactos y detecta conflictos cuando una
misma estación, sensor y fecha presentan valores distintos.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from vigia.dominio.clima import ObservacionClimatica


class ErrorConflictoObservacionIdeam(RuntimeError):
    """Existen observaciones incompatibles para una misma identidad temporal."""


@dataclass(frozen=True, slots=True)
class ResultadoNormalizacionIdeam:
    """Resultado auditable de la normalización."""

    observaciones: tuple[ObservacionClimatica, ...]
    duplicados_eliminados: int


def _clave_temporal(
    observacion: ObservacionClimatica,
) -> tuple[str, str, object]:
    """Identifica una medición de un sensor en un instante determinado."""
    return (
        observacion.codigo_estacion,
        observacion.codigo_sensor,
        observacion.fecha,
    )


def normalizar_observaciones_ideam(
    observaciones: Iterable[ObservacionClimatica],
) -> ResultadoNormalizacionIdeam:
    """
    Elimina duplicados exactos y rechaza observaciones contradictorias.

    Dos observaciones con la misma estación, sensor y fecha deben representar
    exactamente la misma medición. Si difieren en valor, unidad o variable,
    la fuente se considera conflictiva y no se corrige silenciosamente.
    """
    unicas: dict[
        tuple[str, str, object],
        ObservacionClimatica,
    ] = {}

    duplicados = 0

    for observacion in observaciones:
        clave = _clave_temporal(observacion)

        existente = unicas.get(clave)

        if existente is None:
            unicas[clave] = observacion
            continue

        if existente == observacion:
            duplicados += 1
            continue

        raise ErrorConflictoObservacionIdeam(
            "Observaciones IDEAM contradictorias para "
            f"estación={observacion.codigo_estacion!r}, "
            f"sensor={observacion.codigo_sensor!r}, "
            f"fecha={observacion.fecha.isoformat()!r}."
        )

    return ResultadoNormalizacionIdeam(
        observaciones=tuple(unicas.values()),
        duplicados_eliminados=duplicados,
    )
