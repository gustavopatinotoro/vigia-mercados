"""
Contratos para series climáticas agregadas por territorio DIVIPOLA.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from vigia.dominio.clima.modelos import VariableClimatica


@dataclass(frozen=True, slots=True)
class ObservacionClimaticaTerritorial:
    """
    Observación climática agregada para un territorio DIVIPOLA.

    Representa un valor climático consolidado a partir de una o más
    estaciones IDEAM asociadas al mismo territorio y periodo temporal.
    """

    codigo_divipola: str
    variable: VariableClimatica
    fecha: datetime
    valor: Decimal
    unidad: str
    estaciones_utilizadas: int
    observaciones_utilizadas: int

    def __post_init__(self) -> None:
        _validar_codigo_divipola(self.codigo_divipola)

        if not self.unidad.strip():
            raise ValueError("unidad no puede estar vacía.")

        if self.estaciones_utilizadas <= 0:
            raise ValueError("estaciones_utilizadas debe ser mayor que cero.")

        if self.observaciones_utilizadas <= 0:
            raise ValueError("observaciones_utilizadas debe ser mayor que cero.")

        if self.observaciones_utilizadas < self.estaciones_utilizadas:
            raise ValueError(
                "observaciones_utilizadas no puede ser menor que estaciones_utilizadas."
            )

        _validar_precipitacion_no_negativa(
            variable=self.variable,
            valor=self.valor,
        )


@dataclass(frozen=True, slots=True)
class ObservacionClimaticaTerritorialHoraria:
    """
    Observación climática territorial normalizada a una ventana horaria.

    El valor territorial representa la media aritmética no ponderada
    entre los valores horarios de las estaciones disponibles en el
    territorio.

    observaciones_fuente conserva cuántas observaciones originales
    contribuyeron indirectamente al valor territorial.
    """

    codigo_divipola: str
    variable: VariableClimatica
    fecha_hora: datetime
    valor: Decimal
    unidad: str
    estaciones_utilizadas: int
    observaciones_fuente: int

    def __post_init__(self) -> None:
        _validar_codigo_divipola(self.codigo_divipola)

        if not self.unidad.strip():
            raise ValueError("unidad no puede estar vacía.")

        if (
            self.fecha_hora.minute != 0
            or self.fecha_hora.second != 0
            or self.fecha_hora.microsecond != 0
        ):
            raise ValueError("fecha_hora debe representar el inicio exacto de una hora.")

        if self.estaciones_utilizadas <= 0:
            raise ValueError("estaciones_utilizadas debe ser mayor que cero.")

        if self.observaciones_fuente <= 0:
            raise ValueError("observaciones_fuente debe ser mayor que cero.")

        if self.observaciones_fuente < self.estaciones_utilizadas:
            raise ValueError("observaciones_fuente no puede ser menor que estaciones_utilizadas.")

        _validar_precipitacion_no_negativa(
            variable=self.variable,
            valor=self.valor,
        )


def _validar_codigo_divipola(
    codigo_divipola: str,
) -> None:
    """Valida un código DIVIPOLA municipal de cinco dígitos."""
    if len(codigo_divipola) != 5:
        raise ValueError("codigo_divipola debe contener exactamente 5 caracteres.")

    if not codigo_divipola.isdigit():
        raise ValueError("codigo_divipola debe contener únicamente dígitos.")


def _validar_precipitacion_no_negativa(
    *,
    variable: VariableClimatica,
    valor: Decimal,
) -> None:
    """Impide representar precipitación territorial negativa."""
    if variable is VariableClimatica.PRECIPITACION and valor < Decimal("0"):
        raise ValueError("La precipitación territorial no puede ser negativa.")
