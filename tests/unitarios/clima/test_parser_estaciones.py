"""
Pruebas del parser del catálogo nacional de estaciones IDEAM.
"""

from decimal import Decimal

import pytest

from vigia.infraestructura.ideam.parser_estaciones import (
    ErrorParserEstacionIdeam,
    parsear_estaciones_ideam,
)


def _registro_estacion() -> dict[str, object]:
    """Construye un registro representativo del catálogo IDEAM."""
    return {
        "codigo": "0024030700",
        "nombre": "COVARACHIA [24030700]",
        "categoria": "Pluviométrica",
        "tecnologia": "Convencional",
        "estado": "Activa",
        "departamento": "Boyacá",
        "municipio": "Covarachía",
        "altitud": "2244",
        "longitud": "-72.739228889",
        "latitud": "6.500608056",
        "entidad": ("INSTITUTO DE HIDROLOGÍA METEOROLOGÍA Y ESTUDIOS AMBIENTALES"),
    }


def test_parsea_estacion() -> None:
    """Convierte correctamente una estación IDEAM."""
    estaciones = list(parsear_estaciones_ideam([_registro_estacion()]))

    assert len(estaciones) == 1

    estacion = estaciones[0]

    assert estacion.codigo == "0024030700"
    assert estacion.municipio == "Covarachía"
    assert estacion.altitud_m == Decimal("2244")
    assert estacion.latitud == Decimal("6.500608056")
    assert estacion.longitud == Decimal("-72.739228889")


def test_permite_altitud_ausente() -> None:
    """La altitud puede no estar disponible."""
    registro = _registro_estacion()
    registro.pop("altitud")

    estaciones = list(parsear_estaciones_ideam([registro]))

    assert estaciones[0].altitud_m is None


def test_permite_altitud_vacia() -> None:
    """Una altitud vacía se interpreta como dato no disponible."""
    registro = _registro_estacion()
    registro["altitud"] = " "

    estaciones = list(parsear_estaciones_ideam([registro]))

    assert estaciones[0].altitud_m is None


def test_rechaza_coordenada_invalida() -> None:
    """Detecta coordenadas no numéricas."""
    registro = _registro_estacion()
    registro["latitud"] = "sin-dato"

    with pytest.raises(
        ErrorParserEstacionIdeam,
        match="Valor decimal IDEAM inválido",
    ):
        list(parsear_estaciones_ideam([registro]))


def test_rechaza_campo_obligatorio_faltante() -> None:
    """Detecta cambios incompatibles en el esquema del catálogo."""
    registro = _registro_estacion()
    del registro["municipio"]

    with pytest.raises(
        ErrorParserEstacionIdeam,
        match="Campos faltantes",
    ):
        list(parsear_estaciones_ideam([registro]))
