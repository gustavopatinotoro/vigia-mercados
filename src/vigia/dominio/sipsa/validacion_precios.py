"""
Validación de claves candidatas de las series mensuales SIPSA.

Las fuentes históricas pueden contener más de una observación para la misma
combinación de mes, producto y mercado. Estos casos se conservan y se
representan explícitamente como conflictos de fuente.

Este módulo nunca deduplica, promedia ni selecciona observaciones.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from vigia.dominio.sipsa.series_precios import (
    ObservacionPrecioMensualSipsa,
)

ClavePrecioMensualSipsa = tuple[
    date,
    str,
    str,
]


@dataclass(frozen=True, slots=True)
class ConflictoClavePrecioMensualSipsa:
    """Conjunto de observaciones que comparten una clave candidata."""

    clave: ClavePrecioMensualSipsa
    observaciones: tuple[
        ObservacionPrecioMensualSipsa,
        ...,
    ]

    def __post_init__(self) -> None:
        """Valida que el conflicto contenga evidencia coherente."""
        if len(self.observaciones) < 2:
            raise ValueError("Un conflicto requiere al menos dos observaciones.")

        if any(observacion.clave_natural != self.clave for observacion in self.observaciones):
            raise ValueError(
                "Todas las observaciones del conflicto deben compartir la misma clave."
            )


def detectar_conflictos_precios_mensuales(
    observaciones: Iterable[ObservacionPrecioMensualSipsa],
) -> tuple[ConflictoClavePrecioMensualSipsa, ...]:
    """
    Detecta claves candidatas repetidas sin modificar las observaciones.

    Una repetición se considera conflicto incluso cuando todos sus valores
    son idénticos. La interpretación del conflicto corresponde a etapas
    posteriores de calidad de datos.
    """
    primera_por_clave: dict[
        ClavePrecioMensualSipsa,
        ObservacionPrecioMensualSipsa,
    ] = {}

    conflictos: dict[
        ClavePrecioMensualSipsa,
        list[ObservacionPrecioMensualSipsa],
    ] = {}

    for observacion in observaciones:
        clave = observacion.clave_natural

        primera = primera_por_clave.get(clave)

        if primera is None:
            primera_por_clave[clave] = observacion
            continue

        grupo_conflicto = conflictos.get(clave)

        if grupo_conflicto is None:
            grupo_conflicto = [primera]
            conflictos[clave] = grupo_conflicto

        grupo_conflicto.append(observacion)

    return tuple(
        ConflictoClavePrecioMensualSipsa(
            clave=clave,
            observaciones=tuple(conflictos[clave]),
        )
        for clave in sorted(conflictos)
    )
