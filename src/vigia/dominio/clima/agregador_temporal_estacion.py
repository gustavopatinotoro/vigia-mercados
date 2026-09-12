"""
Agregación temporal horaria de observaciones climáticas por estación.

Las observaciones deben haber sido normalizadas, deduplicadas y
consolidadas previamente a nivel de sensor.

Reglas temporales:

- precipitación: suma de los valores dentro de la hora;
- temperatura: media aritmética de los valores dentro de la hora.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from vigia.dominio.clima.modelos import (
    ObservacionClimatica,
    VariableClimatica,
)


class ErrorAgregacionTemporalEstacion(RuntimeError):
    """Error al construir una observación climática horaria de estación."""


@dataclass(frozen=True, slots=True)
class ObservacionClimaticaEstacionHoraria:
    """Valor climático horario consolidado para una estación IDEAM."""

    codigo_estacion: str
    variable: VariableClimatica
    fecha_hora: datetime
    valor: Decimal
    unidad: str
    observaciones_utilizadas: int

    def __post_init__(self) -> None:
        if not self.codigo_estacion.strip():
            raise ValueError("codigo_estacion no puede estar vacío.")

        if not self.unidad.strip():
            raise ValueError("unidad no puede estar vacía.")

        if self.observaciones_utilizadas <= 0:
            raise ValueError("observaciones_utilizadas debe ser mayor que cero.")

        if (
            self.fecha_hora.minute != 0
            or self.fecha_hora.second != 0
            or self.fecha_hora.microsecond != 0
        ):
            raise ValueError("fecha_hora debe representar el inicio exacto de una hora.")

        if self.variable is VariableClimatica.PRECIPITACION and self.valor < Decimal("0"):
            raise ValueError("La precipitación horaria no puede ser negativa.")


@dataclass(frozen=True, slots=True)
class _ClaveHoraEstacion:
    """Identidad de una ventana horaria para una estación."""

    codigo_estacion: str
    variable: VariableClimatica
    fecha_hora: datetime


def agregar_observaciones_horarias_estacion(
    observaciones: Iterable[ObservacionClimatica],
) -> tuple[ObservacionClimaticaEstacionHoraria, ...]:
    """
    Consolida observaciones climáticas en ventanas horarias por estación.

    Se presupone que la entrada contiene como máximo una observación
    canónica por estación, variable e instante.
    """
    grupos: defaultdict[
        _ClaveHoraEstacion,
        list[ObservacionClimatica],
    ] = defaultdict(list)

    for observacion in observaciones:
        fecha_hora = observacion.fecha.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        clave = _ClaveHoraEstacion(
            codigo_estacion=observacion.codigo_estacion,
            variable=observacion.variable,
            fecha_hora=fecha_hora,
        )

        grupos[clave].append(observacion)

    resultados: list[ObservacionClimaticaEstacionHoraria] = []

    for clave, grupo in grupos.items():
        resultados.append(
            _agregar_grupo(
                clave=clave,
                observaciones=grupo,
            )
        )

    resultados.sort(
        key=lambda observacion: (
            observacion.codigo_estacion,
            observacion.variable.value,
            observacion.fecha_hora,
        )
    )

    return tuple(resultados)


def _agregar_grupo(
    *,
    clave: _ClaveHoraEstacion,
    observaciones: list[ObservacionClimatica],
) -> ObservacionClimaticaEstacionHoraria:
    """Aplica la regla temporal correspondiente a la variable."""
    if not observaciones:
        raise ErrorAgregacionTemporalEstacion("No es posible agregar un grupo horario vacío.")

    unidades = {observacion.unidad for observacion in observaciones}

    if len(unidades) != 1:
        raise ErrorAgregacionTemporalEstacion(
            "Una estación presenta unidades incompatibles dentro "
            f"de una misma hora: {sorted(unidades)!r}."
        )

    unidad = next(iter(unidades))

    valores = [observacion.valor for observacion in observaciones]

    if clave.variable is VariableClimatica.PRECIPITACION:
        valor = sum(
            valores,
            start=Decimal("0"),
        )

    elif clave.variable is VariableClimatica.TEMPERATURA:
        valor = sum(
            valores,
            start=Decimal("0"),
        ) / Decimal(len(valores))

    else:
        raise ErrorAgregacionTemporalEstacion(
            f"Variable climática sin regla temporal: {clave.variable!r}."
        )

    return ObservacionClimaticaEstacionHoraria(
        codigo_estacion=clave.codigo_estacion,
        variable=clave.variable,
        fecha_hora=clave.fecha_hora,
        valor=valor,
        unidad=unidad,
        observaciones_utilizadas=len(observaciones),
    )
