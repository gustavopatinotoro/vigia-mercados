"""
Agregación básica de observaciones climáticas por territorio DIVIPOLA.

Esta implementación constituye una línea base determinista:
para un mismo territorio, variable e instante temporal calcula la media
aritmética no ponderada de las observaciones disponibles.

No implementa todavía ponderación espacial ni interpolación climática.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from vigia.dominio.clima.modelos import (
    ObservacionClimatica,
    VariableClimatica,
)
from vigia.dominio.clima.series_territoriales import (
    ObservacionClimaticaTerritorial,
)


class ErrorAgregacionClimaticaTerritorial(RuntimeError):
    """Error al consolidar observaciones climáticas por territorio."""


@dataclass(frozen=True, slots=True)
class _ClaveAgregacion:
    """Identidad temporal de una observación climática territorial."""

    codigo_divipola: str
    variable: VariableClimatica
    fecha: datetime


@dataclass(slots=True)
class _GrupoObservaciones:
    """Acumulador interno para un territorio, variable e instante."""

    unidad: str
    valores: list[Decimal]
    estaciones: set[str]


def agregar_observaciones_territoriales(
    observaciones: Iterable[ObservacionClimatica],
    *,
    divipola_por_estacion: Mapping[str, str],
) -> tuple[ObservacionClimaticaTerritorial, ...]:
    """
    Agrega observaciones IDEAM por DIVIPOLA, variable e instante.

    Las estaciones deben haber sido territorializadas previamente.
    Una estación sin correspondencia DIVIPOLA produce un error explícito
    en lugar de descartarse silenciosamente.
    """
    grupos: dict[
        _ClaveAgregacion,
        _GrupoObservaciones,
    ] = {}

    for observacion in observaciones:
        codigo_divipola = divipola_por_estacion.get(observacion.codigo_estacion)

        if codigo_divipola is None:
            raise ErrorAgregacionClimaticaTerritorial(
                f"No existe territorio DIVIPOLA para la estación {observacion.codigo_estacion!r}."
            )

        _validar_codigo_divipola(codigo_divipola)

        clave = _ClaveAgregacion(
            codigo_divipola=codigo_divipola,
            variable=observacion.variable,
            fecha=observacion.fecha,
        )

        grupo = grupos.get(clave)

        if grupo is None:
            grupos[clave] = _GrupoObservaciones(
                unidad=observacion.unidad,
                valores=[observacion.valor],
                estaciones={observacion.codigo_estacion},
            )
            continue

        if grupo.unidad != observacion.unidad:
            raise ErrorAgregacionClimaticaTerritorial(
                "Unidades incompatibles para una misma agregación "
                f"territorial: {grupo.unidad!r} y "
                f"{observacion.unidad!r}."
            )

        grupo.valores.append(observacion.valor)
        grupo.estaciones.add(observacion.codigo_estacion)

    resultados = [
        ObservacionClimaticaTerritorial(
            codigo_divipola=clave.codigo_divipola,
            variable=clave.variable,
            fecha=clave.fecha,
            valor=_media(grupo.valores),
            unidad=grupo.unidad,
            estaciones_utilizadas=len(grupo.estaciones),
            observaciones_utilizadas=len(grupo.valores),
        )
        for clave, grupo in grupos.items()
    ]

    resultados.sort(
        key=lambda resultado: (
            resultado.codigo_divipola,
            resultado.variable.value,
            resultado.fecha,
        )
    )

    return tuple(resultados)


def _media(
    valores: list[Decimal],
) -> Decimal:
    """Calcula una media aritmética exacta sobre Decimal."""
    if not valores:
        raise ErrorAgregacionClimaticaTerritorial(
            "No es posible calcular la media de un grupo vacío."
        )

    return sum(
        valores,
        start=Decimal("0"),
    ) / Decimal(len(valores))


def _validar_codigo_divipola(
    codigo_divipola: str,
) -> None:
    """Valida la identidad territorial recibida por el agregador."""
    if len(codigo_divipola) != 5 or not codigo_divipola.isdigit():
        raise ErrorAgregacionClimaticaTerritorial(
            f"Código DIVIPOLA inválido para agregación territorial: {codigo_divipola!r}."
        )
