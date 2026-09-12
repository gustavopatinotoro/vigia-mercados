"""
Infraestructura para adquisición y persistencia de información climática.
"""

from vigia.infraestructura.clima.persistencia_series import (
    ResultadoPersistenciaSerieClimatica,
    persistir_series_territoriales_horarias,
)

__all__ = [
    "ResultadoPersistenciaSerieClimatica",
    "persistir_series_territoriales_horarias",
]
