"""
Infraestructura de integración con SIPSA.

Expone la interfaz pública de los adaptadores utilizados para adquirir
e interpretar las fuentes externas publicadas por el DANE.
"""

from vigia.infraestructura.sipsa.descargador import (
    ErrorDescargaSipsa,
    ResultadoDescargaSipsa,
    descargar_xlsx_sipsa,
)
from vigia.infraestructura.sipsa.parser_abastecimiento import (
    ErrorParserAbastecimientoSipsa,
    parsear_abastecimiento_sipsa,
)
from vigia.infraestructura.sipsa.parser_precios import (
    ErrorParserPreciosSipsa,
    parsear_precios_sipsa,
)

__all__ = [
    "ErrorDescargaSipsa",
    "ErrorParserAbastecimientoSipsa",
    "ErrorParserPreciosSipsa",
    "ResultadoDescargaSipsa",
    "descargar_xlsx_sipsa",
    "parsear_abastecimiento_sipsa",
    "parsear_precios_sipsa",
]
