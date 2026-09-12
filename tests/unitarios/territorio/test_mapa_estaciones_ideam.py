"""
Pruebas del resultado de territorialización del catálogo IDEAM.
"""

from decimal import Decimal

import pytest

from vigia.dominio.clima import EstacionIdeam
from vigia.infraestructura.territorio import (
    ResultadoMapaEstacionesIdeam,
)


def _estacion(
    codigo: str,
) -> EstacionIdeam:
    return EstacionIdeam(
        codigo=codigo,
        nombre=f"ESTACION {codigo}",
        categoria="Climatológica",
        tecnologia="Automática",
        estado="Activa",
        departamento="Caldas",
        municipio="Manizales",
        latitud=Decimal("5.07"),
        longitud=Decimal("-75.52"),
        altitud_m=Decimal("2100"),
        entidad="IDEAM",
    )


def test_crea_resultado_completo() -> None:
    resultado = ResultadoMapaEstacionesIdeam(
        divipola_por_estacion={
            "001": "17001",
            "002": "17174",
        },
        estaciones_totales=3,
        estaciones_resueltas=2,
        estaciones_no_resueltas=(_estacion("003"),),
    )

    assert resultado.estaciones_totales == 3
    assert resultado.estaciones_resueltas == 2
    assert len(resultado.estaciones_no_resueltas) == 1
    assert resultado.divipola_por_estacion["001"] == "17001"


def test_permite_cobertura_total() -> None:
    resultado = ResultadoMapaEstacionesIdeam(
        divipola_por_estacion={
            "001": "17001",
        },
        estaciones_totales=1,
        estaciones_resueltas=1,
        estaciones_no_resueltas=(),
    )

    assert resultado.estaciones_no_resueltas == ()


def test_rechaza_total_negativo() -> None:
    with pytest.raises(
        ValueError,
        match="estaciones_totales no puede ser negativo",
    ):
        ResultadoMapaEstacionesIdeam(
            divipola_por_estacion={},
            estaciones_totales=-1,
            estaciones_resueltas=0,
            estaciones_no_resueltas=(),
        )


def test_rechaza_resueltas_mayor_que_total() -> None:
    with pytest.raises(
        ValueError,
        match="no puede superar",
    ):
        ResultadoMapaEstacionesIdeam(
            divipola_por_estacion={
                "001": "17001",
            },
            estaciones_totales=0,
            estaciones_resueltas=1,
            estaciones_no_resueltas=(),
        )


def test_rechaza_conservacion_inconsistente() -> None:
    with pytest.raises(
        ValueError,
        match="no conserva el número total",
    ):
        ResultadoMapaEstacionesIdeam(
            divipola_por_estacion={
                "001": "17001",
            },
            estaciones_totales=3,
            estaciones_resueltas=1,
            estaciones_no_resueltas=(),
        )


def test_rechaza_tamano_de_mapa_inconsistente() -> None:
    with pytest.raises(
        ValueError,
        match="no coincide con el número",
    ):
        ResultadoMapaEstacionesIdeam(
            divipola_por_estacion={
                "001": "17001",
            },
            estaciones_totales=2,
            estaciones_resueltas=2,
            estaciones_no_resueltas=(),
        )
