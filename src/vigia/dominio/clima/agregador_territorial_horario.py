"""
Agregación climática horaria por territorio DIVIPOLA.

Recibe observaciones previamente consolidadas a nivel de estación y hora.
Para cada territorio, variable y hora calcula la media aritmética no
ponderada entre estaciones.

No realiza suma de precipitación entre estaciones: la precipitación ya fue
acumulada temporalmente dentro de cada estación antes de esta etapa.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from vigia.dominio.clima.agregador_temporal_estacion import (
    ObservacionClimaticaEstacionHoraria,
)
from vigia.dominio.clima.modelos import VariableClimatica
from vigia.dominio.clima.series_territoriales import (
    ObservacionClimaticaTerritorialHoraria,
)


class ErrorAgregacionClimaticaTerritorialHoraria(RuntimeError):
    """Error al consolidar observaciones horarias por territorio."""


@dataclass(frozen=True, slots=True)
class _ClaveAgregacionHoraria:
    """Identidad de una ventana climática territorial horaria."""

    codigo_divipola: str
    variable: VariableClimatica
    fecha_hora: datetime


@dataclass(slots=True)
class _GrupoHoraria:
    """Acumulador interno de estaciones para una ventana territorial."""

    unidad: str
    valores_por_estacion: dict[str, Decimal]
    observaciones_fuente: int


def agregar_observaciones_territoriales_horarias(
    observaciones: Iterable[ObservacionClimaticaEstacionHoraria],
    *,
    divipola_por_estacion: Mapping[str, str],
) -> tuple[ObservacionClimaticaTerritorialHoraria, ...]:
    """
    Agrega observaciones estación-hora por territorio DIVIPOLA.

    Cada estación contribuye como máximo una vez a cada combinación
    territorio + variable + hora.

    Una estación sin correspondencia DIVIPOLA produce un error explícito.
    """
    grupos: dict[
        _ClaveAgregacionHoraria,
        _GrupoHoraria,
    ] = {}

    for observacion in observaciones:
        codigo_divipola = divipola_por_estacion.get(observacion.codigo_estacion)

        if codigo_divipola is None:
            raise ErrorAgregacionClimaticaTerritorialHoraria(
                f"No existe territorio DIVIPOLA para la estación {observacion.codigo_estacion!r}."
            )

        _validar_codigo_divipola(codigo_divipola)

        clave = _ClaveAgregacionHoraria(
            codigo_divipola=codigo_divipola,
            variable=observacion.variable,
            fecha_hora=observacion.fecha_hora,
        )

        grupo = grupos.get(clave)

        if grupo is None:
            grupos[clave] = _GrupoHoraria(
                unidad=observacion.unidad,
                valores_por_estacion={
                    observacion.codigo_estacion: observacion.valor,
                },
                observaciones_fuente=observacion.observaciones_utilizadas,
            )
            continue

        if grupo.unidad != observacion.unidad:
            raise ErrorAgregacionClimaticaTerritorialHoraria(
                "Unidades incompatibles para una misma agregación "
                f"territorial horaria: {grupo.unidad!r} y "
                f"{observacion.unidad!r}."
            )

        if observacion.codigo_estacion in grupo.valores_por_estacion:
            raise ErrorAgregacionClimaticaTerritorialHoraria(
                "La estación aparece más de una vez dentro de la misma "
                "ventana territorial horaria: "
                f"{observacion.codigo_estacion!r}, "
                f"{codigo_divipola!r}, "
                f"{observacion.variable.value!r}, "
                f"{observacion.fecha_hora!r}."
            )

        grupo.valores_por_estacion[observacion.codigo_estacion] = observacion.valor

        grupo.observaciones_fuente += observacion.observaciones_utilizadas

    resultados = [
        ObservacionClimaticaTerritorialHoraria(
            codigo_divipola=clave.codigo_divipola,
            variable=clave.variable,
            fecha_hora=clave.fecha_hora,
            valor=_media(list(grupo.valores_por_estacion.values())),
            unidad=grupo.unidad,
            estaciones_utilizadas=len(grupo.valores_por_estacion),
            observaciones_fuente=grupo.observaciones_fuente,
        )
        for clave, grupo in grupos.items()
    ]

    resultados.sort(
        key=lambda resultado: (
            resultado.codigo_divipola,
            resultado.variable.value,
            resultado.fecha_hora,
        )
    )

    return tuple(resultados)


def _media(
    valores: list[Decimal],
) -> Decimal:
    """Calcula una media aritmética exacta sobre Decimal."""
    if not valores:
        raise ErrorAgregacionClimaticaTerritorialHoraria(
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
        raise ErrorAgregacionClimaticaTerritorialHoraria(
            f"Código DIVIPOLA inválido para agregación territorial horaria: {codigo_divipola!r}."
        )
