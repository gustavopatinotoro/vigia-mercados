"""
Modelos canónicos de identidad territorial nacional.

DIVIPOLA constituye la identidad territorial primaria utilizada por VIGÍA
para relacionar fuentes públicas heterogéneas.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class TipoEntidadTerritorial(StrEnum):
    """Tipos territoriales observados en DIVIPOLA."""

    MUNICIPIO = "Municipio"
    AREA_NO_MUNICIPALIZADA = "Área no municipalizada"
    ISLA = "Isla"


@dataclass(frozen=True, slots=True)
class EntidadTerritorialCanonica:
    """Entidad territorial canónica identificada mediante DIVIPOLA."""

    codigo_divipola: str
    codigo_departamento: str
    departamento: str
    nombre: str
    tipo: TipoEntidadTerritorial
    latitud: Decimal
    longitud: Decimal

    def __post_init__(self) -> None:
        if len(self.codigo_divipola) != 5:
            raise ValueError("codigo_divipola debe contener exactamente 5 caracteres.")

        if not self.codigo_divipola.isdigit():
            raise ValueError("codigo_divipola debe contener únicamente dígitos.")

        if len(self.codigo_departamento) != 2:
            raise ValueError("codigo_departamento debe contener exactamente 2 caracteres.")

        if not self.codigo_departamento.isdigit():
            raise ValueError("codigo_departamento debe contener únicamente dígitos.")

        if not self.departamento.strip():
            raise ValueError("departamento no puede estar vacío.")

        if not self.nombre.strip():
            raise ValueError("nombre no puede estar vacío.")

        if self.latitud < Decimal("-90") or self.latitud > Decimal("90"):
            raise ValueError("latitud fuera del rango válido.")

        if self.longitud < Decimal("-180") or self.longitud > Decimal("180"):
            raise ValueError("longitud fuera del rango válido.")
