"""
Contratos de dominio para información SIPSA.

Este paquete contiene representaciones internas independientes del formato
externo utilizado por DANE en archivos Excel u otras fuentes.
"""

from vigia.dominio.sipsa.modelos import (
    RegistroAbastecimiento,
    RegistroPrecioMayorista,
)

__all__ = [
    "RegistroAbastecimiento",
    "RegistroPrecioMayorista",
]
