"""
Consolidación de observaciones climáticas a nivel de estación.

Evita que múltiples canales o sensores equivalentes de una misma estación
sean contabilizados varias veces durante la agregación territorial.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from vigia.dominio.clima.modelos import (
    ObservacionClimatica,
    VariableClimatica,
)


class ErrorConsolidacionClimaticaEstacion(RuntimeError):
    """Error al consolidar sensores de una estación climática."""


@dataclass(frozen=True, slots=True)
class _ClaveEstacion:
    """Identidad de una observación climática a nivel de estación."""

    codigo_estacion: str
    variable: VariableClimatica
    fecha: datetime


_PRIORIDAD_SENSORES: dict[
    VariableClimatica,
    tuple[str, ...],
] = {
    VariableClimatica.PRECIPITACION: (
        "0240",
        "0257",
    ),
    VariableClimatica.TEMPERATURA: (
        "0068",
        "0071",
    ),
}


def consolidar_observaciones_estacion(
    observaciones: Iterable[ObservacionClimatica],
) -> tuple[ObservacionClimatica, ...]:
    """
    Produce como máximo una observación por estación, variable e instante.

    Para grupos multisensor conocidos aplica una prioridad explícita.
    Los grupos desconocidos no se promedian ni se seleccionan
    arbitrariamente.
    """
    grupos: defaultdict[
        _ClaveEstacion,
        list[ObservacionClimatica],
    ] = defaultdict(list)

    for observacion in observaciones:
        grupos[
            _ClaveEstacion(
                codigo_estacion=observacion.codigo_estacion,
                variable=observacion.variable,
                fecha=observacion.fecha,
            )
        ].append(observacion)

    consolidadas: list[ObservacionClimatica] = []

    for clave, grupo in grupos.items():
        consolidadas.append(
            _consolidar_grupo(
                clave=clave,
                observaciones=grupo,
            )
        )

    consolidadas.sort(
        key=lambda observacion: (
            observacion.codigo_estacion,
            observacion.variable.value,
            observacion.fecha,
        )
    )

    return tuple(consolidadas)


def _consolidar_grupo(
    *,
    clave: _ClaveEstacion,
    observaciones: list[ObservacionClimatica],
) -> ObservacionClimatica:
    """Selecciona una única observación representativa del grupo."""
    if not observaciones:
        raise ErrorConsolidacionClimaticaEstacion("No es posible consolidar un grupo vacío.")

    unidades = {observacion.unidad for observacion in observaciones}

    if len(unidades) != 1:
        raise ErrorConsolidacionClimaticaEstacion(
            "Una estación presenta unidades incompatibles para "
            f"{clave.codigo_estacion!r}, "
            f"{clave.variable.value!r}, "
            f"{clave.fecha!r}: {sorted(unidades)!r}."
        )

    if len(observaciones) == 1:
        return observaciones[0]

    por_sensor: dict[str, ObservacionClimatica] = {}

    for observacion in observaciones:
        if observacion.codigo_sensor in por_sensor:
            raise ErrorConsolidacionClimaticaEstacion(
                "Existen múltiples observaciones para el mismo sensor "
                f"{observacion.codigo_sensor!r} en "
                f"{clave.codigo_estacion!r}, {clave.fecha!r}."
            )

        por_sensor[observacion.codigo_sensor] = observacion

    prioridad = _PRIORIDAD_SENSORES.get(clave.variable)

    if prioridad is None:
        raise ErrorConsolidacionClimaticaEstacion(
            f"No existe política de sensores para la variable {clave.variable.value!r}."
        )

    sensores_observados = set(por_sensor)

    sensores_permitidos = set(prioridad)

    if not sensores_observados.issubset(sensores_permitidos):
        raise ErrorConsolidacionClimaticaEstacion(
            "Combinación multisensor no reconocida para "
            f"{clave.codigo_estacion!r}, "
            f"{clave.variable.value!r}, "
            f"{clave.fecha!r}: "
            f"{sorted(sensores_observados)!r}."
        )

    for codigo_sensor in prioridad:
        seleccionada = por_sensor.get(codigo_sensor)

        if seleccionada is not None:
            return seleccionada

    raise ErrorConsolidacionClimaticaEstacion(
        "No fue posible seleccionar una observación representativa."
    )
