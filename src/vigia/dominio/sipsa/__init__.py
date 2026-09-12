"""
Contratos de dominio para información SIPSA.

Este paquete contiene representaciones internas independientes del formato
externo utilizado por DANE en archivos Excel, CSV u otras fuentes.
"""

from vigia.dominio.sipsa.modelos import (
    RegistroAbastecimiento,
    RegistroPrecioMayorista,
)
from vigia.dominio.sipsa.series_abastecimiento import (
    ClaveAbastecimientoDiarioSipsa,
    ObservacionAbastecimientoDiarioSipsa,
)
from vigia.dominio.sipsa.series_precios import (
    ObservacionPrecioMensualSipsa,
)
from vigia.dominio.sipsa.validacion_precios import (
    ClavePrecioMensualSipsa,
    ConflictoClavePrecioMensualSipsa,
    detectar_conflictos_precios_mensuales,
)

__all__ = [
    "ClaveAbastecimientoDiarioSipsa",
    "ClavePrecioMensualSipsa",
    "ConflictoClavePrecioMensualSipsa",
    "ObservacionAbastecimientoDiarioSipsa",
    "ObservacionPrecioMensualSipsa",
    "RegistroAbastecimiento",
    "RegistroPrecioMayorista",
    "detectar_conflictos_precios_mensuales",
]
