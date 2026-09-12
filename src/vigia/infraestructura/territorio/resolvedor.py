"""
Resolución territorial entre fuentes públicas heterogéneas.

Asocia entidades externas con identidades territoriales nacionales
canónicas basadas en DIVIPOLA y alias explícitos auditables.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from vigia.dominio.clima import EstacionIdeam
from vigia.dominio.territorio import (
    AliasTerritorial,
    EntidadTerritorialCanonica,
)
from vigia.infraestructura.territorio.normalizador import (
    normalizar_nombre_territorial,
)


class ErrorResolucionTerritorial(RuntimeError):
    """Error al resolver una entidad contra el catálogo territorial."""


@dataclass(frozen=True, slots=True)
class EstacionIdeamResuelta:
    """Estación IDEAM asociada a una entidad territorial canónica."""

    estacion: EstacionIdeam
    territorio: EntidadTerritorialCanonica


class ResolvedorTerritorial:
    """Resuelve territorios externos contra DIVIPOLA."""

    def __init__(
        self,
        entidades: Iterable[EntidadTerritorialCanonica],
        *,
        alias: Iterable[AliasTerritorial] = (),
    ) -> None:
        self._por_nombre: dict[
            tuple[str, str],
            EntidadTerritorialCanonica,
        ] = {}

        self._por_divipola: dict[
            str,
            EntidadTerritorialCanonica,
        ] = {}

        self._alias: dict[
            tuple[str, str, str],
            EntidadTerritorialCanonica,
        ] = {}

        for entidad in entidades:
            if entidad.codigo_divipola in self._por_divipola:
                raise ErrorResolucionTerritorial(
                    f"Código DIVIPOLA duplicado en catálogo: {entidad.codigo_divipola!r}."
                )

            clave = (
                normalizar_nombre_territorial(entidad.departamento),
                normalizar_nombre_territorial(entidad.nombre),
            )

            existente = self._por_nombre.get(clave)

            if existente is not None and existente.codigo_divipola != entidad.codigo_divipola:
                raise ErrorResolucionTerritorial(
                    "Colisión territorial tras normalización: "
                    f"{entidad.departamento!r}, "
                    f"{entidad.nombre!r}."
                )

            self._por_divipola[entidad.codigo_divipola] = entidad

            self._por_nombre[clave] = entidad

        for alias_territorial in alias:
            territorio = self._por_divipola.get(alias_territorial.codigo_divipola)

            if territorio is None:
                raise ErrorResolucionTerritorial(
                    "Alias referencia un código DIVIPOLA desconocido: "
                    f"{alias_territorial.codigo_divipola!r}."
                )

            clave_alias = (
                alias_territorial.fuente.strip().casefold(),
                normalizar_nombre_territorial(alias_territorial.departamento_fuente),
                normalizar_nombre_territorial(alias_territorial.nombre_fuente),
            )

            existente_alias = self._alias.get(clave_alias)

            if (
                existente_alias is not None
                and existente_alias.codigo_divipola != territorio.codigo_divipola
            ):
                raise ErrorResolucionTerritorial(
                    "Alias territorial contradictorio para "
                    f"{alias_territorial.fuente!r}, "
                    f"{alias_territorial.departamento_fuente!r}, "
                    f"{alias_territorial.nombre_fuente!r}."
                )

            self._alias[clave_alias] = territorio

    def resolver_por_nombre(
        self,
        *,
        departamento: str,
        nombre: str,
    ) -> EntidadTerritorialCanonica:
        """Resuelve una entidad mediante nombres normalizados."""
        clave = (
            normalizar_nombre_territorial(departamento),
            normalizar_nombre_territorial(nombre),
        )

        resultado = self._por_nombre.get(clave)

        if resultado is None:
            raise ErrorResolucionTerritorial(
                f"No existe correspondencia territorial para {departamento!r}, {nombre!r}."
            )

        return resultado

    def resolver_por_alias(
        self,
        *,
        fuente: str,
        departamento: str,
        nombre: str,
    ) -> EntidadTerritorialCanonica:
        """Resuelve una entidad mediante un alias explícito."""
        clave = (
            fuente.strip().casefold(),
            normalizar_nombre_territorial(departamento),
            normalizar_nombre_territorial(nombre),
        )

        resultado = self._alias.get(clave)

        if resultado is None:
            raise ErrorResolucionTerritorial(
                f"No existe alias territorial para {fuente!r}, {departamento!r}, {nombre!r}."
            )

        return resultado

    def resolver_por_divipola(
        self,
        codigo_divipola: str,
    ) -> EntidadTerritorialCanonica:
        """Resuelve directamente una identidad territorial DIVIPOLA."""
        resultado = self._por_divipola.get(codigo_divipola)

        if resultado is None:
            raise ErrorResolucionTerritorial(f"Código DIVIPOLA desconocido: {codigo_divipola!r}.")

        return resultado

    def resolver_estacion_ideam(
        self,
        estacion: EstacionIdeam,
    ) -> EstacionIdeamResuelta:
        """
        Asocia una estación IDEAM con su territorio canónico.

        Primero intenta resolución nominal exacta normalizada. Si falla,
        consulta únicamente alias IDEAM explícitamente declarados.
        """
        try:
            territorio = self.resolver_por_nombre(
                departamento=estacion.departamento,
                nombre=estacion.municipio,
            )
        except ErrorResolucionTerritorial:
            territorio = self.resolver_por_alias(
                fuente="IDEAM",
                departamento=estacion.departamento,
                nombre=estacion.municipio,
            )

        return EstacionIdeamResuelta(
            estacion=estacion,
            territorio=territorio,
        )
