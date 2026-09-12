"""
Pruebas unitarias del cliente geoespacial MGN.
"""

from decimal import Decimal

import pytest

from vigia.infraestructura.territorio.cliente_mgn import (
    ClienteMgn,
    ErrorClienteMgn,
    ErrorConflictoGeoespacialMgn,
    MunicipioMgn,
)


def test_interpreta_municipio_mgn() -> None:
    datos: object = {
        "features": [
            {
                "attributes": {
                    "MPIO_CDPMP": "05664",
                    "DPTO_CNMBRE": "ANTIOQUIA",
                    "MPIO_CNMBRE": "SAN PEDRO DE LOS MILAGROS",
                }
            }
        ]
    }

    resultado = ClienteMgn._interpretar_respuesta(datos)

    assert resultado == MunicipioMgn(
        codigo_divipola="05664",
        departamento="ANTIOQUIA",
        municipio="SAN PEDRO DE LOS MILAGROS",
    )


def test_retorna_none_sin_interseccion() -> None:
    datos: object = {
        "features": [],
    }

    assert ClienteMgn._interpretar_respuesta(datos) is None


def test_rechaza_multiples_intersecciones() -> None:
    datos: object = {
        "features": [
            {
                "attributes": {
                    "MPIO_CDPMP": "05664",
                    "DPTO_CNMBRE": "ANTIOQUIA",
                    "MPIO_CNMBRE": "SAN PEDRO DE LOS MILAGROS",
                }
            },
            {
                "attributes": {
                    "MPIO_CDPMP": "05308",
                    "DPTO_CNMBRE": "ANTIOQUIA",
                    "MPIO_CNMBRE": "GIRARDOTA",
                }
            },
        ]
    }

    with pytest.raises(
        ErrorConflictoGeoespacialMgn,
        match="más de un municipio",
    ):
        ClienteMgn._interpretar_respuesta(datos)


def test_rechaza_error_arcgis() -> None:
    datos: object = {
        "error": {
            "code": 400,
            "message": "Invalid query",
        }
    }

    with pytest.raises(
        ErrorClienteMgn,
        match="MGN reportó error",
    ):
        ClienteMgn._interpretar_respuesta(datos)


def test_rechaza_respuesta_sin_features() -> None:
    with pytest.raises(
        ErrorClienteMgn,
        match="falta 'features'",
    ):
        ClienteMgn._interpretar_respuesta({})


def test_rechaza_codigo_divipola_invalido() -> None:
    datos: object = {
        "features": [
            {
                "attributes": {
                    "MPIO_CDPMP": "5664",
                    "DPTO_CNMBRE": "ANTIOQUIA",
                    "MPIO_CNMBRE": "SAN PEDRO DE LOS MILAGROS",
                }
            }
        ]
    }

    with pytest.raises(
        ErrorClienteMgn,
        match="Municipio MGN inválido",
    ):
        ClienteMgn._interpretar_respuesta(datos)


def test_rechaza_latitud_fuera_de_rango() -> None:
    with pytest.raises(
        ValueError,
        match="latitud fuera",
    ):
        ClienteMgn._validar_coordenadas(
            latitud=Decimal("91"),
            longitud=Decimal("-75"),
        )


def test_rechaza_longitud_fuera_de_rango() -> None:
    with pytest.raises(
        ValueError,
        match="longitud fuera",
    ):
        ClienteMgn._validar_coordenadas(
            latitud=Decimal("5"),
            longitud=Decimal("-181"),
        )
