"""
Pruebas del parser DIVIPOLA.
"""

from decimal import Decimal

import pytest

from vigia.dominio.territorio import TipoEntidadTerritorial
from vigia.infraestructura.territorio.parser_divipola import (
    ErrorParserDivipola,
    parsear_divipola,
)


def _registro() -> dict[str, object]:
    """Construye un registro representativo DIVIPOLA."""
    return {
        "cod_dpto": "17",
        "dpto": "CALDAS",
        "cod_mpio": "17001",
        "nom_mpio": "MANIZALES",
        "tipo_municipio": "Municipio",
        "latitud": "5.06889",
        "longitud": "-75.51738",
    }


def test_parsea_municipio() -> None:
    """Convierte correctamente un municipio."""
    entidades = list(parsear_divipola([_registro()]))

    assert len(entidades) == 1

    entidad = entidades[0]

    assert entidad.codigo_divipola == "17001"
    assert entidad.nombre == "MANIZALES"
    assert entidad.tipo is TipoEntidadTerritorial.MUNICIPIO
    assert entidad.latitud == Decimal("5.06889")


def test_parsea_coordenada_con_coma_decimal() -> None:
    """Acepta la notación decimal con coma observada en DIVIPOLA real."""
    registro = _registro()
    registro["latitud"] = "6,246631"
    registro["longitud"] = "-75,123456"

    entidad = next(parsear_divipola([registro]))

    assert entidad.latitud == Decimal("6.246631")
    assert entidad.longitud == Decimal("-75.123456")


def test_parsea_area_no_municipalizada() -> None:
    """Reconoce áreas no municipalizadas."""
    registro = _registro()
    registro["cod_dpto"] = "97"
    registro["dpto"] = "VAUPÉS"
    registro["cod_mpio"] = "97511"
    registro["nom_mpio"] = "PACOA"
    registro["tipo_municipio"] = "Área no municipalizada"

    entidad = next(parsear_divipola([registro]))

    assert entidad.tipo is TipoEntidadTerritorial.AREA_NO_MUNICIPALIZADA


def test_parsea_isla() -> None:
    """Reconoce la categoría Isla."""
    registro = _registro()
    registro["cod_dpto"] = "88"
    registro["cod_mpio"] = "88001"
    registro["dpto"] = "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA"
    registro["nom_mpio"] = "SAN ANDRÉS"
    registro["tipo_municipio"] = "Isla"

    entidad = next(parsear_divipola([registro]))

    assert entidad.tipo is TipoEntidadTerritorial.ISLA


def test_rechaza_tipo_desconocido() -> None:
    """Detecta tipos territoriales no soportados."""
    registro = _registro()
    registro["tipo_municipio"] = "Tipo nuevo"

    with pytest.raises(
        ErrorParserDivipola,
        match="Tipo territorial DIVIPOLA desconocido",
    ):
        list(parsear_divipola([registro]))


def test_rechaza_decimal_invalido() -> None:
    """Rechaza coordenadas que no representan números."""
    registro = _registro()
    registro["latitud"] = "sin-dato"

    with pytest.raises(
        ErrorParserDivipola,
        match="Valor decimal DIVIPOLA inválido",
    ):
        list(parsear_divipola([registro]))


def test_rechaza_campo_faltante() -> None:
    """Detecta registros incompletos."""
    registro = _registro()
    del registro["cod_mpio"]

    with pytest.raises(
        ErrorParserDivipola,
        match="Campos faltantes",
    ):
        list(parsear_divipola([registro]))
