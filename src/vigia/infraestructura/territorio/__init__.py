"""
Infraestructura para resolución y normalización territorial.
"""

from vigia.infraestructura.territorio.alias_ideam import ALIAS_IDEAM
from vigia.infraestructura.territorio.catalogo_divipola import (
    DATASET_DIVIPOLA,
    cargar_catalogo_divipola,
)
from vigia.infraestructura.territorio.cliente_mgn import (
    ClienteMgn,
    ErrorClienteMgn,
    ErrorConflictoGeoespacialMgn,
    MunicipioMgn,
)
from vigia.infraestructura.territorio.mapa_estaciones_ideam import (
    DATASET_ESTACIONES_IDEAM,
    ClienteCatalogoEstacionesIdeamProtocolo,
    ResultadoMapaEstacionesIdeam,
    construir_mapa_estaciones_ideam,
)
from vigia.infraestructura.territorio.normalizador import (
    normalizar_nombre_territorial,
)
from vigia.infraestructura.territorio.parser_divipola import (
    ErrorParserDivipola,
    parsear_divipola,
)
from vigia.infraestructura.territorio.resolvedor import (
    ErrorResolucionTerritorial,
    EstacionIdeamResuelta,
    ResolvedorTerritorial,
)
from vigia.infraestructura.territorio.resolvedor_geoespacial import (
    ClienteMgnProtocolo,
    ResolvedorTerritorialGeoespacial,
)

__all__ = [
    "ALIAS_IDEAM",
    "DATASET_DIVIPOLA",
    "DATASET_ESTACIONES_IDEAM",
    "ClienteCatalogoEstacionesIdeamProtocolo",
    "ClienteMgn",
    "ClienteMgnProtocolo",
    "ErrorClienteMgn",
    "ErrorConflictoGeoespacialMgn",
    "ErrorParserDivipola",
    "ErrorResolucionTerritorial",
    "EstacionIdeamResuelta",
    "MunicipioMgn",
    "ResolvedorTerritorial",
    "ResolvedorTerritorialGeoespacial",
    "ResultadoMapaEstacionesIdeam",
    "cargar_catalogo_divipola",
    "construir_mapa_estaciones_ideam",
    "normalizar_nombre_territorial",
    "parsear_divipola",
]
