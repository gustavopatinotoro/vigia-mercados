"""
Pruebas de agregación climática horaria por estación.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima import (
    ErrorAgregacionTemporalEstacion,
    ObservacionClimatica,
    ObservacionClimaticaEstacionHoraria,
    VariableClimatica,
    agregar_observaciones_horarias_estacion,
)


def _observacion(
    *,
    estacion: str = "001",
    sensor: str = "0240",
    variable: VariableClimatica,
    fecha: datetime,
    valor: str,
    unidad: str,
) -> ObservacionClimatica:
    return ObservacionClimatica(
        codigo_estacion=estacion,
        codigo_sensor=sensor,
        fecha=fecha,
        variable=variable,
        valor=Decimal(valor),
        unidad=unidad,
        nombre_estacion=f"ESTACION {estacion}",
        departamento="CALDAS",
        municipio="MANIZALES",
        latitud=Decimal("5.07"),
        longitud=Decimal("-75.52"),
        descripcion_sensor="SENSOR",
    )


def test_suma_precipitacion_dentro_de_la_hora() -> None:
    observaciones = [
        _observacion(
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12, 0),
            valor="0.2",
            unidad="mm",
        ),
        _observacion(
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12, 10),
            valor="0.4",
            unidad="mm",
        ),
        _observacion(
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12, 20),
            valor="1.0",
            unidad="mm",
        ),
    ]

    resultados = agregar_observaciones_horarias_estacion(observaciones)

    assert len(resultados) == 1

    resultado = resultados[0]

    assert resultado.fecha_hora == datetime(2026, 9, 1, 12)
    assert resultado.valor == Decimal("1.6")
    assert resultado.observaciones_utilizadas == 3


def test_promedia_temperatura_dentro_de_la_hora() -> None:
    observaciones = [
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12, 0),
            valor="18",
            unidad="°C",
        ),
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12, 20),
            valor="20",
            unidad="°C",
        ),
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12, 40),
            valor="22",
            unidad="°C",
        ),
    ]

    resultados = agregar_observaciones_horarias_estacion(observaciones)

    assert len(resultados) == 1
    assert resultados[0].valor == Decimal("20")
    assert resultados[0].observaciones_utilizadas == 3


def test_separa_horas() -> None:
    observaciones = [
        _observacion(
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12, 50),
            valor="1",
            unidad="mm",
        ),
        _observacion(
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 13, 0),
            valor="2",
            unidad="mm",
        ),
    ]

    resultados = agregar_observaciones_horarias_estacion(observaciones)

    assert len(resultados) == 2
    assert resultados[0].fecha_hora == datetime(2026, 9, 1, 12)
    assert resultados[1].fecha_hora == datetime(2026, 9, 1, 13)


def test_separa_estaciones() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12, 0),
            valor="1",
            unidad="mm",
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12, 0),
            valor="2",
            unidad="mm",
        ),
    ]

    resultados = agregar_observaciones_horarias_estacion(observaciones)

    assert len(resultados) == 2


def test_separa_variables() -> None:
    observaciones = [
        _observacion(
            sensor="0240",
            variable=VariableClimatica.PRECIPITACION,
            fecha=datetime(2026, 9, 1, 12),
            valor="1",
            unidad="mm",
        ),
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12),
            valor="20",
            unidad="°C",
        ),
    ]

    resultados = agregar_observaciones_horarias_estacion(observaciones)

    assert len(resultados) == 2


def test_rechaza_unidades_incompatibles_en_misma_hora() -> None:
    observaciones = [
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12),
            valor="20",
            unidad="°C",
        ),
        _observacion(
            sensor="0068",
            variable=VariableClimatica.TEMPERATURA,
            fecha=datetime(2026, 9, 1, 12, 30),
            valor="293",
            unidad="K",
        ),
    ]

    with pytest.raises(
        ErrorAgregacionTemporalEstacion,
        match="unidades incompatibles",
    ):
        agregar_observaciones_horarias_estacion(observaciones)


def test_contrato_rechaza_hora_no_normalizada() -> None:
    with pytest.raises(
        ValueError,
        match="inicio exacto de una hora",
    ):
        ObservacionClimaticaEstacionHoraria(
            codigo_estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            fecha_hora=datetime(2026, 9, 1, 12, 30),
            valor=Decimal("20"),
            unidad="°C",
            observaciones_utilizadas=1,
        )


def test_contrato_rechaza_precipitacion_negativa() -> None:
    with pytest.raises(
        ValueError,
        match="precipitación horaria no puede ser negativa",
    ):
        ObservacionClimaticaEstacionHoraria(
            codigo_estacion="001",
            variable=VariableClimatica.PRECIPITACION,
            fecha_hora=datetime(2026, 9, 1, 12),
            valor=Decimal("-1"),
            unidad="mm",
            observaciones_utilizadas=1,
        )


def test_entrada_vacia_produce_resultado_vacio() -> None:
    assert agregar_observaciones_horarias_estacion([]) == ()
