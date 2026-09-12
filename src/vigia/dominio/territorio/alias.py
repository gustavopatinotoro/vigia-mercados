"""
Contratos para alias territoriales entre fuentes externas y DIVIPOLA.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AliasTerritorial:
    """
    Asociación explícita entre un nombre territorial externo y DIVIPOLA.

    Un alias representa una decisión auditable; nunca una aproximación
    probabilística o una coincidencia difusa.
    """

    fuente: str
    departamento_fuente: str
    nombre_fuente: str
    codigo_divipola: str

    def __post_init__(self) -> None:
        if not self.fuente.strip():
            raise ValueError("fuente no puede estar vacía.")

        if not self.departamento_fuente.strip():
            raise ValueError("departamento_fuente no puede estar vacío.")

        if not self.nombre_fuente.strip():
            raise ValueError("nombre_fuente no puede estar vacío.")

        if len(self.codigo_divipola) != 5:
            raise ValueError("codigo_divipola debe contener exactamente 5 caracteres.")

        if not self.codigo_divipola.isdigit():
            raise ValueError("codigo_divipola debe contener únicamente dígitos.")
