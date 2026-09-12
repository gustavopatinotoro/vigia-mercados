"""
Modelos canónicos de información agroclimática.

Estos modelos representan estaciones y observaciones IDEAM ya validadas,
independientemente del formato utilizado por Socrata.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class VariableClimatica(StrEnum):
    """Variables climáticas inicialmente soportadas por VIGÍA."""

    PRECIPITACION = "precipitacion"
    TEMPERATURA = "temperatura"


def _validar_texto(valor: str, campo: str) -> None:
    """Valida campos textuales obligatorios."""
    if not valor.strip():
        raise ValueError(f"{campo} no puede estar vacío.")


def _validar_latitud(valor: Decimal) -> None:
    """Valida una latitud geográfica."""
    if valor < Decimal("-90") or valor > Decimal("90"):
        raise ValueError("latitud fuera del rango válido.")


def _validar_longitud(valor: Decimal) -> None:
    """Valida una longitud geográfica."""
    if valor < Decimal("-180") or valor > Decimal("180"):
        raise ValueError("longitud fuera del rango válido.")


@dataclass(frozen=True, slots=True)
class EstacionIdeam:
    """Representación canónica de una estación IDEAM."""

    codigo: str
    nombre: str
    categoria: str
    tecnologia: str
    estado: str
    departamento: str
    municipio: str
    latitud: Decimal
    longitud: Decimal
    altitud_m: Decimal | None
    entidad: str

    def __post_init__(self) -> None:
        """Comprueba invariantes de la estación."""
        _validar_texto(self.codigo, "codigo")
        _validar_texto(self.nombre, "nombre")
        _validar_texto(self.departamento, "departamento")
        _validar_texto(self.municipio, "municipio")
        _validar_texto(self.estado, "estado")

        _validar_latitud(self.latitud)
        _validar_longitud(self.longitud)


@dataclass(frozen=True, slots=True)
class ObservacionClimatica:
    """Observación climática individual proveniente de IDEAM."""

    codigo_estacion: str
    codigo_sensor: str
    fecha: datetime
    variable: VariableClimatica
    valor: Decimal
    unidad: str
    nombre_estacion: str
    departamento: str
    municipio: str
    latitud: Decimal
    longitud: Decimal
    descripcion_sensor: str
    fuente: str = "IDEAM"

    def __post_init__(self) -> None:
        """Comprueba invariantes de la observación."""
        _validar_texto(self.codigo_estacion, "codigo_estacion")
        _validar_texto(self.codigo_sensor, "codigo_sensor")
        _validar_texto(self.unidad, "unidad")
        _validar_texto(self.nombre_estacion, "nombre_estacion")
        _validar_texto(self.departamento, "departamento")
        _validar_texto(self.municipio, "municipio")

        _validar_latitud(self.latitud)
        _validar_longitud(self.longitud)

        if self.variable is VariableClimatica.PRECIPITACION and self.valor < 0:
            raise ValueError("La precipitación observada no puede ser negativa.")
