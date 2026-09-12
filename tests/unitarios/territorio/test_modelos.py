"""
Pruebas de contratos territoriales nacionales.
"""

from decimal import Decimal

import pytest

from vigia.dominio.territorio import (
    EntidadTerritorialCanonica,
    TipoEntidadTerritorial,
)


def _entidad() -> EntidadTerritorialCanonica:
    return EntidadTerritorialCanonica(
        codigo_divipola="17001",
        codigo_departamento="17",
        departamento="CALDAS",
        nombre="MANIZALES",
        tipo=TipoEntidadTerritorial.MUNICIPIO,
        latitud=Decimal("5.06889"),
        longitud=Decimal("-75.51738"),
    )


def test_crea_entidad_territorial() -> None:
    """Acepta una entidad DIVIPOLA válida."""
    entidad = _entidad()

    assert entidad.codigo_divipola == "17001"
    assert entidad.nombre == "MANIZALES"


def test_permite_area_no_municipalizada() -> None:
    """Representa territorios nacionales que no son municipios."""
    entidad = EntidadTerritorialCanonica(
        codigo_divipola="97511",
        codigo_departamento="97",
        departamento="VAUPÉS",
        nombre="PACOA",
        tipo=TipoEntidadTerritorial.AREA_NO_MUNICIPALIZADA,
        latitud=Decimal("0.0"),
        longitud=Decimal("-70.0"),
    )

    assert entidad.tipo is TipoEntidadTerritorial.AREA_NO_MUNICIPALIZADA


def test_permite_isla() -> None:
    """Representa la categoría territorial Isla de DIVIPOLA."""
    entidad = EntidadTerritorialCanonica(
        codigo_divipola="88001",
        codigo_departamento="88",
        departamento=("ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA"),
        nombre="SAN ANDRÉS",
        tipo=TipoEntidadTerritorial.ISLA,
        latitud=Decimal("12.5"),
        longitud=Decimal("-81.7"),
    )

    assert entidad.tipo is TipoEntidadTerritorial.ISLA


def test_rechaza_divipola_invalido() -> None:
    """El código territorial debe conservar formato DIVIPOLA."""
    with pytest.raises(
        ValueError,
        match="exactamente 5 caracteres",
    ):
        EntidadTerritorialCanonica(
            codigo_divipola="1701",
            codigo_departamento="17",
            departamento="CALDAS",
            nombre="MANIZALES",
            tipo=TipoEntidadTerritorial.MUNICIPIO,
            latitud=Decimal("5"),
            longitud=Decimal("-75"),
        )


def test_rechaza_coordenadas_invalidas() -> None:
    """Impide coordenadas geográficas imposibles."""
    with pytest.raises(
        ValueError,
        match="latitud fuera del rango válido",
    ):
        EntidadTerritorialCanonica(
            codigo_divipola="17001",
            codigo_departamento="17",
            departamento="CALDAS",
            nombre="MANIZALES",
            tipo=TipoEntidadTerritorial.MUNICIPIO,
            latitud=Decimal("100"),
            longitud=Decimal("-75"),
        )
