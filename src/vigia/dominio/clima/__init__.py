"""
Contratos públicos del dominio agroclimático.
"""

from vigia.dominio.clima.agregador_temporal_estacion import (
    ErrorAgregacionTemporalEstacion,
    ObservacionClimaticaEstacionHoraria,
    agregar_observaciones_horarias_estacion,
)
from vigia.dominio.clima.agregador_territorial import (
    ErrorAgregacionClimaticaTerritorial,
    agregar_observaciones_territoriales,
)
from vigia.dominio.clima.agregador_territorial_horario import (
    ErrorAgregacionClimaticaTerritorialHoraria,
    agregar_observaciones_territoriales_horarias,
)
from vigia.dominio.clima.consolidador_estacion import (
    ErrorConsolidacionClimaticaEstacion,
    consolidar_observaciones_estacion,
)
from vigia.dominio.clima.modelos import (
    EstacionIdeam,
    ObservacionClimatica,
    VariableClimatica,
)
from vigia.dominio.clima.series_territoriales import (
    ObservacionClimaticaTerritorial,
    ObservacionClimaticaTerritorialHoraria,
)

__all__ = [
    "ErrorAgregacionClimaticaTerritorial",
    "ErrorAgregacionClimaticaTerritorialHoraria",
    "ErrorAgregacionTemporalEstacion",
    "ErrorConsolidacionClimaticaEstacion",
    "EstacionIdeam",
    "ObservacionClimatica",
    "ObservacionClimaticaEstacionHoraria",
    "ObservacionClimaticaTerritorial",
    "ObservacionClimaticaTerritorialHoraria",
    "VariableClimatica",
    "agregar_observaciones_horarias_estacion",
    "agregar_observaciones_territoriales",
    "agregar_observaciones_territoriales_horarias",
    "consolidar_observaciones_estacion",
]
