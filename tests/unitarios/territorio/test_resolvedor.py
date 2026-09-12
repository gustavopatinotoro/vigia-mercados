"""
Pruebas del resolver territorial canónico.
"""

from decimal import Decimal

import pytest

from vigia.dominio.clima import EstacionIdeam
from vigia.dominio.territorio import (
    AliasTerritorial,
    EntidadTerritorialCanonica,
    TipoEntidadTerritorial,
)
from vigia.infraestructura.territorio import (
    ErrorResolucionTerritorial,
    ResolvedorTerritorial,
)


def _entidad(
    codigo: str,
    nombre: str,
) -> EntidadTerritorialCanonica:
    return EntidadTerritorialCanonica(
        codigo_divipola=codigo,
        codigo_departamento="17",
        departamento="CALDAS",
        nombre=nombre,
        tipo=TipoEntidadTerritorial.MUNICIPIO,
        latitud=Decimal("5"),
        longitud=Decimal("-75"),
    )


def _catalogo() -> list[EntidadTerritorialCanonica]:
    return [
        _entidad("17001", "MANIZALES"),
        _entidad("17174", "CHINCHINÁ"),
        _entidad("17873", "VILLAMARÍA"),
    ]


def _estacion(
    municipio: str,
) -> EstacionIdeam:
    return EstacionIdeam(
        codigo="001",
        nombre="ESTACION",
        categoria="Climatológica",
        tecnologia="Automática",
        estado="Activa",
        departamento="Caldas",
        municipio=municipio,
        latitud=Decimal("5"),
        longitud=Decimal("-75"),
        altitud_m=Decimal("2000"),
        entidad="IDEAM",
    )


def test_resuelve_nombre_normalizado() -> None:
    resolvedor = ResolvedorTerritorial(_catalogo())

    entidad = resolvedor.resolver_por_nombre(
        departamento="Caldas",
        nombre="Manizales",
    )

    assert entidad.codigo_divipola == "17001"


def test_resuelve_nombre_sin_tilde() -> None:
    resolvedor = ResolvedorTerritorial(_catalogo())

    entidad = resolvedor.resolver_por_nombre(
        departamento="Caldas",
        nombre="Chinchina",
    )

    assert entidad.codigo_divipola == "17174"


def test_resuelve_alias_explicito() -> None:
    alias = AliasTerritorial(
        fuente="IDEAM",
        departamento_fuente="Caldas",
        nombre_fuente="Capital Caldense",
        codigo_divipola="17001",
    )

    resolvedor = ResolvedorTerritorial(
        _catalogo(),
        alias=[alias],
    )

    entidad = resolvedor.resolver_por_alias(
        fuente="IDEAM",
        departamento="Caldas",
        nombre="Capital Caldense",
    )

    assert entidad.codigo_divipola == "17001"


def test_resuelve_estacion_mediante_alias() -> None:
    alias = AliasTerritorial(
        fuente="IDEAM",
        departamento_fuente="Caldas",
        nombre_fuente="Capital Caldense",
        codigo_divipola="17001",
    )

    resolvedor = ResolvedorTerritorial(
        _catalogo(),
        alias=[alias],
    )

    resultado = resolvedor.resolver_estacion_ideam(_estacion("Capital Caldense"))

    assert resultado.territorio.codigo_divipola == "17001"


def test_resuelve_divipola_directamente() -> None:
    resolvedor = ResolvedorTerritorial(_catalogo())

    entidad = resolvedor.resolver_por_divipola("17873")

    assert entidad.nombre == "VILLAMARÍA"


def test_rechaza_entidad_desconocida() -> None:
    resolvedor = ResolvedorTerritorial(_catalogo())

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="No existe alias territorial",
    ):
        resolvedor.resolver_estacion_ideam(_estacion("Territorio inexistente"))


def test_rechaza_alias_con_divipola_desconocido() -> None:
    alias = AliasTerritorial(
        fuente="IDEAM",
        departamento_fuente="Caldas",
        nombre_fuente="Prueba",
        codigo_divipola="17999",
    )

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="DIVIPOLA desconocido",
    ):
        ResolvedorTerritorial(
            _catalogo(),
            alias=[alias],
        )


def test_rechaza_alias_contradictorio() -> None:
    alias = [
        AliasTerritorial(
            fuente="IDEAM",
            departamento_fuente="Caldas",
            nombre_fuente="Prueba",
            codigo_divipola="17001",
        ),
        AliasTerritorial(
            fuente="IDEAM",
            departamento_fuente="Caldas",
            nombre_fuente="Prueba",
            codigo_divipola="17174",
        ),
    ]

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="Alias territorial contradictorio",
    ):
        ResolvedorTerritorial(
            _catalogo(),
            alias=alias,
        )


def test_rechaza_divipola_duplicado() -> None:
    entidades = [
        _entidad("17001", "MANIZALES"),
        _entidad("17001", "OTRO"),
    ]

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="DIVIPOLA duplicado",
    ):
        ResolvedorTerritorial(entidades)


def test_rechaza_colision_normalizada() -> None:
    entidades = [
        _entidad("17174", "CHINCHINÁ"),
        _entidad("17999", "CHINCHINA"),
    ]

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="Colisión territorial",
    ):
        ResolvedorTerritorial(entidades)
