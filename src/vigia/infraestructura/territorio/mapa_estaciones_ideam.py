"""
Construcción del mapa territorial nacional de estaciones IDEAM.

Convierte el catálogo completo de estaciones IDEAM en una relación
determinista entre código de estación y código DIVIPOLA, utilizando
la cadena de resolución territorial configurada por VIGÍA.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from vigia.dominio.clima import EstacionIdeam
from vigia.infraestructura.ideam import (
    ClienteIdeam,
    ConsultaSocrata,
    parsear_estaciones_ideam,
)
from vigia.infraestructura.territorio.alias_ideam import ALIAS_IDEAM
from vigia.infraestructura.territorio.catalogo_divipola import (
    cargar_catalogo_divipola,
)
from vigia.infraestructura.territorio.cliente_mgn import ClienteMgn
from vigia.infraestructura.territorio.resolvedor import (
    ErrorResolucionTerritorial,
    ResolvedorTerritorial,
)
from vigia.infraestructura.territorio.resolvedor_geoespacial import (
    ResolvedorTerritorialGeoespacial,
)

DATASET_ESTACIONES_IDEAM = "hp9r-jxuu"


class ClienteCatalogoEstacionesIdeamProtocolo(Protocol):
    """Contrato mínimo requerido para consultar estaciones IDEAM."""

    def consultar(
        self,
        dataset_id: str,
        consulta: ConsultaSocrata | None = None,
        *,
        timeout_segundos: float = 30.0,
    ) -> list[dict[str, object]]:
        """Consulta registros de un dataset Socrata."""
        ...


@dataclass(frozen=True, slots=True)
class ResultadoMapaEstacionesIdeam:
    """Resultado de territorializar el catálogo completo IDEAM."""

    divipola_por_estacion: dict[str, str]
    estaciones_totales: int
    estaciones_resueltas: int
    estaciones_no_resueltas: tuple[EstacionIdeam, ...]

    def __post_init__(self) -> None:
        if self.estaciones_totales < 0:
            raise ValueError("estaciones_totales no puede ser negativo.")

        if self.estaciones_resueltas < 0:
            raise ValueError("estaciones_resueltas no puede ser negativo.")

        if self.estaciones_resueltas > self.estaciones_totales:
            raise ValueError("estaciones_resueltas no puede superar estaciones_totales.")

        esperado = self.estaciones_resueltas + len(self.estaciones_no_resueltas)

        if esperado != self.estaciones_totales:
            raise ValueError("El resultado territorial no conserva el número total de estaciones.")

        if len(self.divipola_por_estacion) != self.estaciones_resueltas:
            raise ValueError(
                "El mapa estación→DIVIPOLA no coincide con el número de estaciones resueltas."
            )


def construir_mapa_estaciones_ideam(
    *,
    cliente_ideam: ClienteCatalogoEstacionesIdeamProtocolo | None = None,
    timeout_segundos: float = 120.0,
    timeout_mgn_segundos: float = 60.0,
) -> ResultadoMapaEstacionesIdeam:
    """
    Territorializa el catálogo IDEAM completo.

    No filtra por estado de la estación. Esto permite resolver también
    observaciones históricas o actuales asociadas a estaciones que el
    catálogo clasifica actualmente como inactivas.
    """
    if timeout_segundos <= 0:
        raise ValueError("timeout_segundos debe ser mayor que cero.")

    if timeout_mgn_segundos <= 0:
        raise ValueError("timeout_mgn_segundos debe ser mayor que cero.")

    cliente = cliente_ideam if cliente_ideam is not None else ClienteIdeam()

    registros = cliente.consultar(
        DATASET_ESTACIONES_IDEAM,
        consulta=ConsultaSocrata(
            limite=15000,
            orden="codigo",
        ),
        timeout_segundos=timeout_segundos,
    )

    estaciones = tuple(parsear_estaciones_ideam(registros))

    catalogo_divipola = cargar_catalogo_divipola(
        timeout_segundos=timeout_segundos,
    )

    resolvedor_base = ResolvedorTerritorial(
        catalogo_divipola,
        alias=ALIAS_IDEAM,
    )

    resolvedor = ResolvedorTerritorialGeoespacial(
        resolvedor_base=resolvedor_base,
        cliente_mgn=ClienteMgn(),
    )

    divipola_por_estacion: dict[str, str] = {}
    no_resueltas: list[EstacionIdeam] = []

    for estacion in estaciones:
        if estacion.codigo in divipola_por_estacion:
            raise ErrorResolucionTerritorial(
                f"Código de estación IDEAM duplicado en el catálogo: {estacion.codigo!r}."
            )

        try:
            resultado = resolvedor.resolver_estacion_ideam(
                estacion,
                timeout_segundos=timeout_mgn_segundos,
            )
        except ErrorResolucionTerritorial:
            no_resueltas.append(estacion)
            continue

        divipola_por_estacion[estacion.codigo] = resultado.territorio.codigo_divipola

    return ResultadoMapaEstacionesIdeam(
        divipola_por_estacion=divipola_por_estacion,
        estaciones_totales=len(estaciones),
        estaciones_resueltas=len(divipola_por_estacion),
        estaciones_no_resueltas=tuple(no_resueltas),
    )
