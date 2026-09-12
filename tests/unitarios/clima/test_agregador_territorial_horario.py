"""
Pruebas de agregación climática territorial horaria.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima import (
    ErrorAgregacionClimaticaTerritorialHoraria,
    ObservacionClimaticaEstacionHoraria,
    ObservacionClimaticaTerritorialHoraria,
    VariableClimatica,
    agregar_observaciones_territoriales_horarias,
)


def _observacion(
    *,
    estacion: str,
    variable: VariableClimatica,
    valor: str,
    unidad: str,
    hora: datetime | None = None,
    observaciones_utilizadas: int = 1,
) -> ObservacionClimaticaEstacionHoraria:
    return ObservacionClimaticaEstacionHoraria(
        codigo_estacion=estacion,
        variable=variable,
        fecha_hora=hora or datetime(2026, 9, 1, 12),
        valor=Decimal(valor),
        unidad=unidad,
        observaciones_utilizadas=observaciones_utilizadas,
    )


def test_promedia_precipitacion_horaria_entre_estaciones() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.PRECIPITACION,
            valor="2",
            unidad="mm",
            observaciones_utilizadas=6,
        ),
        _observacion(
            estacion="002",
            variable=VariableClimatica.PRECIPITACION,
            valor="4",
            unidad="mm",
            observaciones_utilizadas=6,
        ),
    ]

    resultado = agregar_observaciones_territoriales_horarias(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17001",
        },
    )

    assert len(resultado) == 1
    assert resultado[0].valor == Decimal("3")
    assert resultado[0].estaciones_utilizadas == 2
    assert resultado[0].observaciones_fuente == 12


def test_promedia_temperatura_horaria_entre_estaciones() -> None:
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
            valor="22",
            unidad="°C",
        ),
    ]

    resultado = agregar_observaciones_territoriales_horarias(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17001",
        },
    )

    assert resultado[0].valor == Decimal("20")


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
            valor="22",
            unidad="°C",
        ),
    ]

    resultado = agregar_observaciones_territoriales_horarias(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
            "002": "17174",
        },
    )

    assert len(resultado) == 2


def test_separa_horas() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="18",
            unidad="°C",
            hora=datetime(2026, 9, 1, 12),
        ),
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
            hora=datetime(2026, 9, 1, 13),
        ),
    ]

    resultado = agregar_observaciones_territoriales_horarias(
        observaciones,
        divipola_por_estacion={
            "001": "17001",
        },
    )

    assert len(resultado) == 2


def test_rechaza_estacion_sin_divipola() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
    ]

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorialHoraria,
        match="No existe territorio DIVIPOLA",
    ):
        agregar_observaciones_territoriales_horarias(
            observaciones,
            divipola_por_estacion={},
        )


def test_rechaza_codigo_divipola_invalido() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
    ]

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorialHoraria,
        match="Código DIVIPOLA inválido",
    ):
        agregar_observaciones_territoriales_horarias(
            observaciones,
            divipola_por_estacion={
                "001": "17X01",
            },
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
            valor="293",
            unidad="K",
        ),
    ]

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorialHoraria,
        match="Unidades incompatibles",
    ):
        agregar_observaciones_territoriales_horarias(
            observaciones,
            divipola_por_estacion={
                "001": "17001",
                "002": "17001",
            },
        )


def test_rechaza_estacion_duplicada_en_misma_hora() -> None:
    observaciones = [
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="20",
            unidad="°C",
        ),
        _observacion(
            estacion="001",
            variable=VariableClimatica.TEMPERATURA,
            valor="21",
            unidad="°C",
        ),
    ]

    with pytest.raises(
        ErrorAgregacionClimaticaTerritorialHoraria,
        match="aparece más de una vez",
    ):
        agregar_observaciones_territoriales_horarias(
            observaciones,
            divipola_por_estacion={
                "001": "17001",
            },
        )


def test_contrato_horario_rechaza_fecha_no_normalizada() -> None:
    with pytest.raises(
        ValueError,
        match="inicio exacto",
    ):
        ObservacionClimaticaTerritorialHoraria(
            codigo_divipola="17001",
            variable=VariableClimatica.TEMPERATURA,
            fecha_hora=datetime(2026, 9, 1, 12, 30),
            valor=Decimal("20"),
            unidad="°C",
            estaciones_utilizadas=1,
            observaciones_fuente=1,
        )


def test_contrato_horario_rechaza_fuente_menor_que_estaciones() -> None:
    with pytest.raises(
        ValueError,
        match="no puede ser menor",
    ):
        ObservacionClimaticaTerritorialHoraria(
            codigo_divipola="17001",
            variable=VariableClimatica.TEMPERATURA,
            fecha_hora=datetime(2026, 9, 1, 12),
            valor=Decimal("20"),
            unidad="°C",
            estaciones_utilizadas=2,
            observaciones_fuente=1,
        )
