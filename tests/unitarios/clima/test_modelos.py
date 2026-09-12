"""
Pruebas de los contratos canónicos agroclimáticos.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima import (
    EstacionIdeam,
    ObservacionClimatica,
    VariableClimatica,
)


def test_crea_estacion_valida() -> None:
    """Acepta una estación IDEAM válida."""
    estacion = EstacionIdeam(
        codigo="0024030700",
        nombre="COVARACHIA [24030700]",
        categoria="Pluviométrica",
        tecnologia="Convencional",
        estado="Activa",
        departamento="Boyacá",
        municipio="Covarachía",
        latitud=Decimal("6.500608056"),
        longitud=Decimal("-72.739228889"),
        altitud_m=Decimal("2244"),
        entidad="IDEAM",
    )

    assert estacion.codigo == "0024030700"
    assert estacion.municipio == "Covarachía"


def test_rechaza_coordenada_invalida() -> None:
    """Impide estaciones con coordenadas imposibles."""
    with pytest.raises(
        ValueError,
        match="latitud fuera del rango válido",
    ):
        EstacionIdeam(
            codigo="1",
            nombre="Prueba",
            categoria="Pluviométrica",
            tecnologia="Convencional",
            estado="Activa",
            departamento="Caldas",
            municipio="Manizales",
            latitud=Decimal("100"),
            longitud=Decimal("-75"),
            altitud_m=None,
            entidad="IDEAM",
        )


def test_crea_precipitacion_valida() -> None:
    """Acepta una observación de precipitación realista."""
    observacion = ObservacionClimatica(
        codigo_estacion="0048015050",
        codigo_sensor="0257",
        fecha=datetime.fromisoformat("2024-05-07T21:04:00"),
        variable=VariableClimatica.PRECIPITACION,
        valor=Decimal("0"),
        unidad="mm",
        nombre_estacion="AEROPUERTO VASQUEZ COBO",
        departamento="AMAZONAS",
        municipio="LETICIA",
        latitud=Decimal("-4.19386111"),
        longitud=Decimal("-69.94091667"),
        descripcion_sensor="GPRS - PRECIPITACIÓN",
    )

    assert observacion.valor == Decimal("0")
    assert observacion.unidad == "mm"


def test_rechaza_precipitacion_negativa() -> None:
    """Impide valores físicamente inválidos de precipitación."""
    with pytest.raises(
        ValueError,
        match="precipitación observada no puede ser negativa",
    ):
        ObservacionClimatica(
            codigo_estacion="0048015050",
            codigo_sensor="0257",
            fecha=datetime.fromisoformat("2024-05-07T21:04:00"),
            variable=VariableClimatica.PRECIPITACION,
            valor=Decimal("-1"),
            unidad="mm",
            nombre_estacion="ESTACION",
            departamento="AMAZONAS",
            municipio="LETICIA",
            latitud=Decimal("-4"),
            longitud=Decimal("-69"),
            descripcion_sensor="PRECIPITACIÓN",
        )


def test_permite_temperatura_negativa() -> None:
    """La temperatura puede ser inferior a cero."""
    observacion = ObservacionClimatica(
        codigo_estacion="001",
        codigo_sensor="0068",
        fecha=datetime.fromisoformat("2026-01-01T00:00:00"),
        variable=VariableClimatica.TEMPERATURA,
        valor=Decimal("-2.5"),
        unidad="°C",
        nombre_estacion="ESTACION",
        departamento="BOYACÁ",
        municipio="TUNJA",
        latitud=Decimal("5.5"),
        longitud=Decimal("-73.3"),
        descripcion_sensor="Temp Aire 2 m",
    )

    assert observacion.valor == Decimal("-2.5")
