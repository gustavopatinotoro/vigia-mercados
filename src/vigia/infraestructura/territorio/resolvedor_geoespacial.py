"""
Fallback geoespacial para resolución territorial mediante MGN.

El componente preserva la resolución nominal y por alias existente.
Únicamente cuando ambas fallan consulta el polígono municipal oficial
del MGN mediante las coordenadas de la estación IDEAM.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from vigia.dominio.clima import EstacionIdeam
from vigia.infraestructura.territorio.cliente_mgn import MunicipioMgn
from vigia.infraestructura.territorio.resolvedor import (
    ErrorResolucionTerritorial,
    EstacionIdeamResuelta,
    ResolvedorTerritorial,
)


class ClienteMgnProtocolo(Protocol):
    """Contrato mínimo requerido del cliente geoespacial MGN."""

    def resolver_punto(
        self,
        *,
        latitud: Decimal,
        longitud: Decimal,
        timeout_segundos: float = 30.0,
    ) -> MunicipioMgn | None:
        """Resuelve una coordenada WGS84 contra polígonos MGN."""
        ...


class ResolvedorTerritorialGeoespacial:
    """
    Orquesta resolución territorial nominal y geoespacial.

    Orden de resolución:

    1. nombre territorial normalizado;
    2. alias explícito;
    3. intersección geoespacial MGN;
    4. no resuelto.

    Nunca transforma una ausencia de intersección en una asignación
    territorial aproximada.
    """

    def __init__(
        self,
        *,
        resolvedor_base: ResolvedorTerritorial,
        cliente_mgn: ClienteMgnProtocolo,
    ) -> None:
        self._resolvedor_base = resolvedor_base
        self._cliente_mgn = cliente_mgn

    def resolver_estacion_ideam(
        self,
        estacion: EstacionIdeam,
        *,
        timeout_segundos: float = 30.0,
    ) -> EstacionIdeamResuelta:
        """
        Resuelve territorialmente una estación IDEAM.

        El acceso a MGN sólo ocurre cuando la resolución nominal y por
        alias falla.
        """
        try:
            return self._resolvedor_base.resolver_estacion_ideam(estacion)
        except ErrorResolucionTerritorial as error_base:
            municipio_mgn = self._cliente_mgn.resolver_punto(
                latitud=estacion.latitud,
                longitud=estacion.longitud,
                timeout_segundos=timeout_segundos,
            )

            if municipio_mgn is None:
                raise ErrorResolucionTerritorial(
                    "La estación IDEAM no pudo resolverse por nombre, "
                    "alias ni intersección geoespacial MGN: "
                    f"{estacion.codigo!r}, "
                    f"{estacion.departamento!r}, "
                    f"{estacion.municipio!r}."
                ) from error_base

            territorio = self._resolvedor_base.resolver_por_divipola(municipio_mgn.codigo_divipola)

            return EstacionIdeamResuelta(
                estacion=estacion,
                territorio=territorio,
            )
