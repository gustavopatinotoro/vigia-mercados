"""
Casos de uso de VIGÍA.
"""

from vigia.aplicacion.importar_sipsa import (
    ImportacionSipsa,
    importar_archivo_abastecimiento,
    importar_archivo_precios,
)
from vigia.aplicacion.series_abastecimiento import (
    ErrorGeneracionAbastecimiento,
    ResultadoGeneracionAbastecimiento,
    generar_serie_abastecimiento_sipsa,
)
from vigia.aplicacion.series_climaticas import (
    ErrorGeneracionSeriesClimaticas,
    EstadisticasVariableClimatica,
    ResultadoGeneracionSeriesClimaticas,
    generar_series_climaticas_territoriales,
)
from vigia.aplicacion.series_precios import (
    ErrorGeneracionPreciosMensuales,
    EstadisticasArchivoPrecioMensual,
    ResultadoGeneracionPreciosMensuales,
    generar_serie_historica_precios_sipsa,
)

__all__ = [
    "ErrorGeneracionAbastecimiento",
    "ErrorGeneracionPreciosMensuales",
    "ErrorGeneracionSeriesClimaticas",
    "EstadisticasArchivoPrecioMensual",
    "EstadisticasVariableClimatica",
    "ImportacionSipsa",
    "ResultadoGeneracionAbastecimiento",
    "ResultadoGeneracionPreciosMensuales",
    "ResultadoGeneracionSeriesClimaticas",
    "generar_serie_abastecimiento_sipsa",
    "generar_serie_historica_precios_sipsa",
    "generar_series_climaticas_territoriales",
    "importar_archivo_abastecimiento",
    "importar_archivo_precios",
]
