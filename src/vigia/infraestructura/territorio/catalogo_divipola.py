"""
Carga reproducible del catálogo territorial nacional DIVIPOLA.
"""

from __future__ import annotations

from vigia.dominio.territorio import EntidadTerritorialCanonica
from vigia.infraestructura.ideam import (
    ClienteIdeam,
    ConsultaSocrata,
)
from vigia.infraestructura.territorio.parser_divipola import (
    parsear_divipola,
)

DATASET_DIVIPOLA = "gdxc-w37w"


def cargar_catalogo_divipola(
    *,
    cliente: ClienteIdeam | None = None,
    timeout_segundos: float = 120.0,
) -> tuple[EntidadTerritorialCanonica, ...]:
    """Carga el catálogo nacional completo de DIVIPOLA."""
    cliente_socrata = cliente if cliente is not None else ClienteIdeam()

    registros = cliente_socrata.consultar(
        DATASET_DIVIPOLA,
        consulta=ConsultaSocrata(
            limite=5000,
            orden="cod_dpto, cod_mpio",
        ),
        timeout_segundos=timeout_segundos,
    )

    return tuple(parsear_divipola(registros))
