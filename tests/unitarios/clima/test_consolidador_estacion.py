"""
Pruebas de consolidación climática a nivel de estación.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima import (
    ErrorConsolidacionClimaticaEstacion,
    ObservacionClimatica,
    VariableClimatica,
    consolidar_observaciones_estacion,
)


def _observacion(
    *,
    sensor: str,
    variable: VariableClimatica,
    valor: str,
    unidad: str,
    estacion: str = "001",
    fecha: datetime | None = None,
) -> ObservacionClimatica:
    return ObservacionClimatica(
        codigo_estacion=estacion,
        codigo_sensor=sensor,
        fecha=fecha or datetime(2026, 9, 1, 12),
        variable=variable,
        valor=Decimal(valor),
        unidad=unidad,
        nombre_estacion="ESTACION",
        departamento="CALDAS",
        municipio="MANIZALES",
        latitud=Decimal("5.07"),
        longitud=Decimal("-75.52"),
        descripcion_sensor="SENSOR",
    )


def test_conserva_observacion_unica() -> None:
    observacion = _observacion(
        sensor="0240",
        variable=VariableClimatica.PRECIPITACION,
        valor="2",
        unidad="mm",
    )

    resultado = consolidar_observaciones_estacion([observacion])

    assert resultado == (observacion,)


def test_precipitacion_prioriza_sensor_0240() -> None:
    observaciones = [
        _observacion(
            sensor="0257",
            variable=VariableClimatica.PRECIPITACION,
            valor="0.2",
            unidad="mm",
        ),
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            valor="1.4",
            unidad="mm",
        ),
    ]

    resultado = consolidar_observaciones_estacion(observaciones)

    assert len(resultado) == 1
    assert resultado[0].codigo_sensor == "0240"
    assert resultado[0].valor == Decimal("1.4")


def test_temperatura_prioriza_sensor_0068() -> None:
    observaciones = [
        _observacion(
            sensor="0071",
            variable=VariableClimatica.TEMPERATURA,
            valor="23.4",
            unidad="°C",
        ),
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            valor="23.7",
            unidad="°C",
        ),
    ]

    resultado = consolidar_observaciones_estacion(observaciones)

    assert len(resultado) == 1
    assert resultado[0].codigo_sensor == "0068"
    assert resultado[0].valor == Decimal("23.7")


def test_permite_sensor_gprs_como_unica_observacion() -> None:
    observacion = _observacion(
        sensor="0071",
        variable=VariableClimatica.TEMPERATURA,
        valor="20.5",
        unidad="°C",
    )

    resultado = consolidar_observaciones_estacion([observacion])

    assert resultado[0].codigo_sensor == "0071"


def test_separa_estaciones() -> None:
    observaciones = [
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            valor="1",
            unidad="mm",
            estacion="001",
        ),
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            valor="2",
            unidad="mm",
            estacion="002",
        ),
    ]

    resultado = consolidar_observaciones_estacion(observaciones)

    assert len(resultado) == 2


def test_separa_instantes() -> None:
    observaciones = [
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            valor="1",
            unidad="mm",
            fecha=datetime(2026, 9, 1, 12),
        ),
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            valor="2",
            unidad="mm",
            fecha=datetime(2026, 9, 1, 13),
        ),
    ]

    resultado = consolidar_observaciones_estacion(observaciones)

    assert len(resultado) == 2


def test_rechaza_combinacion_multisensor_desconocida() -> None:
    observaciones = [
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            valor="1",
            unidad="mm",
        ),
        _observacion(
            sensor="9999",
            variable=VariableClimatica.PRECIPITACION,
            valor="1",
            unidad="mm",
        ),
    ]

    with pytest.raises(
        ErrorConsolidacionClimaticaEstacion,
        match="Combinación multisensor no reconocida",
    ):
        consolidar_observaciones_estacion(observaciones)


def test_rechaza_unidades_incompatibles() -> None:
    observaciones = [
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
        _observacion(
            sensor="0071",
            variable=VariableClimatica.TEMPERATURA,
            valor="293.15",
            unidad="K",
        ),
    ]

    with pytest.raises(
        ErrorConsolidacionClimaticaEstacion,
        match="unidades incompatibles",
    ):
        consolidar_observaciones_estacion(observaciones)
