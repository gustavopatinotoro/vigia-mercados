"""
Infraestructura de integración con IDEAM.

Expone el cliente Socrata, los parsers y las operaciones de normalización
utilizadas para convertir datos externos de IDEAM en modelos canónicos.
"""

from vigia.infraestructura.ideam.cliente import (
    ClienteIdeam,
    ConsultaSocrata,
    ErrorClienteIdeam,
    PoliticaReintentosIdeam,
)
from vigia.infraestructura.ideam.normalizador_observaciones import (
    ErrorConflictoObservacionIdeam,
    ResultadoNormalizacionIdeam,
    normalizar_observaciones_ideam,
)
from vigia.infraestructura.ideam.parser_estaciones import (
    ErrorParserEstacionIdeam,
    parsear_estaciones_ideam,
)
from vigia.infraestructura.ideam.parser_observaciones import (
    ErrorParserObservacionIdeam,
    parsear_observaciones_ideam,
)

__all__ = [
    "ClienteIdeam",
    "ConsultaSocrata",
    "ErrorClienteIdeam",
    "ErrorConflictoObservacionIdeam",
    "ErrorParserEstacionIdeam",
    "ErrorParserObservacionIdeam",
    "PoliticaReintentosIdeam",
    "ResultadoNormalizacionIdeam",
    "normalizar_observaciones_ideam",
    "parsear_estaciones_ideam",
    "parsear_observaciones_ideam",
]
