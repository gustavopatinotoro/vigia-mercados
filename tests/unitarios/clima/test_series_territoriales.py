"""
Pruebas de los contratos de series climáticas territoriales.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima.modelos import VariableClimatica
from vigia.dominio.clima.series_territoriales import (
    ObservacionClimaticaTerritorial,
)


def test_crea_observacion_territorial_precipitacion() -> None:
    observacion = ObservacionClimaticaTerritorial(
        codigo_divipola="17001",
        variable=VariableClimatica.PRECIPITACION,
        fecha=datetime(2026, 9, 1, 12),
        valor=Decimal("8.25"),
        unidad="mm",
        estaciones_utilizadas=3,
        observaciones_utilizadas=3,
    )

    assert observacion.codigo_divipola == "17001"
    assert observacion.valor == Decimal("8.25")
    assert observacion.estaciones_utilizadas == 3


def test_crea_observacion_territorial_temperatura() -> None:
    observacion = ObservacionClimaticaTerritorial(
        codigo_divipola="17001",
        variable=VariableClimatica.TEMPERATURA,
        fecha=datetime(2026, 9, 1, 12),
        valor=Decimal("18.7"),
        unidad="°C",
        estaciones_utilizadas=4,
        observaciones_utilizadas=4,
    )

    assert observacion.variable is VariableClimatica.TEMPERATURA
    assert observacion.valor == Decimal("18.7")


def test_rechaza_divipola_invalido() -> None:
    with pytest.raises(
        ValueError,
        match="exactamente 5 caracteres",
    ):
        ObservacionClimaticaTerritorial(
            codigo_divipola="1701",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12),
            valor=Decimal("20"),
            unidad="°C",
            estaciones_utilizadas=1,
            observaciones_utilizadas=1,
        )


def test_rechaza_unidad_vacia() -> None:
    with pytest.raises(
        ValueError,
        match="unidad no puede estar vacía",
    ):
        ObservacionClimaticaTerritorial(
            codigo_divipola="17001",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12),
            valor=Decimal("20"),
            unidad=" ",
            estaciones_utilizadas=1,
            observaciones_utilizadas=1,
        )


def test_rechaza_estaciones_cero() -> None:
    with pytest.raises(
        ValueError,
        match="estaciones_utilizadas debe ser mayor que cero",
    ):
        ObservacionClimaticaTerritorial(
            codigo_divipola="17001",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12),
            valor=Decimal("20"),
            unidad="°C",
            estaciones_utilizadas=0,
            observaciones_utilizadas=1,
        )


def test_rechaza_observaciones_menores_que_estaciones() -> None:
    with pytest.raises(
        ValueError,
        match="observaciones_utilizadas no puede ser menor",
    ):
        ObservacionClimaticaTerritorial(
            codigo_divipola="17001",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12),
            valor=Decimal("20"),
            unidad="°C",
            estaciones_utilizadas=3,
            observaciones_utilizadas=2,
        )


def test_rechaza_precipitacion_negativa() -> None:
    with pytest.raises(
        ValueError,
        match="precipitación territorial no puede ser negativa",
    ):
        ObservacionClimaticaTerritorial(
            codigo_divipola="17001",
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12),
            valor=Decimal("-1"),
            unidad="mm",
            estaciones_utilizadas=1,
            observaciones_utilizadas=1,
        )


def test_permite_temperatura_negativa() -> None:
    observacion = ObservacionClimaticaTerritorial(
        codigo_divipola="11001",
        variable=VariableClimatica.TEMPERATURA,
        fecha=datetime(2026, 1, 1, 6),
        valor=Decimal("-2.5"),
        unidad="°C",
        estaciones_utilizadas=1,
        observaciones_utilizadas=1,
    )

    assert observacion.valor == Decimal("-2.5")
