"""
Pruebas del agregador climático territorial.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima import (
    ErrorAgregacionClimaticaTerritorial,
    ObservacionClimatica,
    VariableClimatica,
    agregar_observaciones_territoriales,
)


def _observacion(
    *,
    estacion: str,
    variable: VariableClimatica,
    valor: str,
    unidad: str,
    fecha: datetime | None = None,
) -> ObservacionClimatica:
    return ObservacionClimatica(
        codigo_estacion=estacion,
        codigo_sensor="001",
        fecha=(fecha if fecha is not None else datetime(2026, 9, 1, 12)),
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


def test_agrega_temperatura_de_varias_estaciones() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="18",
            unidad="°C",
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
        _observacion(
            estacion="003",
            variable=VariableClimatica.TEMPERATURA,
            valor="22",
            unidad="°C",
        ),
    ]

    resultados = agregar_observaciones_territoriales(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17001",
            "003": "17001",
        },
    )

    assert len(resultados) == 1

    resultado = resultados[0]

    assert resultado.codigo_divipola == "17001"
    assert resultado.valor == Decimal("20")
    assert resultado.estaciones_utilizadas == 3
    assert resultado.observaciones_utilizadas == 3


def test_agrega_precipitacion_sin_sumar_estaciones() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.PRECIPITACION,
            valor="10",
            unidad="mm",
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.PRECIPITACION,
            valor="20",
            unidad="mm",
        ),
    ]

    resultados = agregar_observaciones_territoriales(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17001",
        },
    )

    assert resultados[0].valor == Decimal("15")


def test_separa_territorios() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="18",
            unidad="°C",
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.TEMPERATURA,
            valor="25",
            unidad="°C",
        ),
    ]

    resultados = agregar_observaciones_territoriales(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17174",
        },
    )

    assert len(resultados) == 2
    assert resultados[0].codigo_divipola == "17001"
    assert resultados[1].codigo_divipola == "17174"


def test_separa_variables() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
        _observacion(
            estacion="001",
            variable=VariableClimatica.PRECIPITACION,
            valor="5",
            unidad="mm",
        ),
    ]

    resultados = agregar_observaciones_territoriales(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
        },
    )

    assert len(resultados) == 2


def test_separa_instantes_temporales() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="18",
            unidad="°C",
            fecha=datetime(2026, 9, 1, 12),
        ),
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
            fecha=datetime(2026, 9, 1, 13),
        ),
    ]

    resultados = agregar_observaciones_territoriales(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
        },
    )

    assert len(resultados) == 2


def test_cuenta_observaciones_y_estaciones_independientemente() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="18",
            unidad="°C",
        ),
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.TEMPERATURA,
            valor="22",
            unidad="°C",
        ),
    ]

    resultados = agregar_observaciones_territoriales(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17001",
        },
    )

    resultado = resultados[0]

    assert resultado.estaciones_utilizadas == 2
    assert resultado.observaciones_utilizadas == 3
    assert resultado.valor == Decimal("20")


def test_rechaza_estacion_sin_territorio() -> None:
    observacion = _observacion(
        estacion="001",
        variable=VariableClimatica.TEMPERATURA,
        valor="20",
        unidad="°C",
    )

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorial,
        match="No existe territorio DIVIPOLA",
    ):
        agregar_observaciones_territoriales(
            [observacion],
            divipola_por_estacion={},
        )


def test_rechaza_unidades_incompatibles() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.TEMPERATURA,
            valor="293.15",
            unidad="K",
        ),
    ]

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorial,
        match="Unidades incompatibles",
    ):
        agregar_observaciones_territoriales(
            observaciones,
            divipola_por_estacion={
                "001": "17001",
                "002": "17001",
            },
        )


def test_rechaza_codigo_divipola_invalido() -> None:
    observacion = _observacion(
        estacion="001",
        variable=VariableClimatica.TEMPERATURA,
        valor="20",
        unidad="°C",
    )

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorial,
        match="Código DIVIPOLA inválido",
    ):
        agregar_observaciones_territoriales(
            [observacion],
            divipola_por_estacion={
                "001": "1701",
            },
        )


def test_entrada_vacia_genera_resultado_vacio() -> None:
    resultados = agregar_observaciones_territoriales(
        [],
        divipola_por_estacion={},
    )

    assert resultados == ()
