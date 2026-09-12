"""
Pruebas de contratos auxiliares del generador climático.
"""

from datetime import datetime

import pytest

from vigia.aplicacion.series_climaticas import (
    _fecha_socrata,
    _nombre_base_predeterminado,
    _validar_parametros,
)


def test_serializa_fecha_socrata() -> None:
    resultado = _fecha_socrata(
        datetime(
            2026,
            9,
            1,
            12,
            30,
            45,
        )
    )

    assert resultado == "2026-09-01T12:30:45.000"


def test_nombre_predeterminado_para_dia_completo() -> None:
    resultado = _nombre_base_predeterminado(
        inicio=datetime(2026, 9, 1),
        fin=datetime(2026, 9, 2),
    )

    assert resultado == "series_territoriales_horarias_2026-09-01"


def test_nombre_predeterminado_para_intervalo_arbitrario() -> None:
    resultado = _nombre_base_predeterminado(
        inicio=datetime(2026, 9, 1, 6),
        fin=datetime(2026, 9, 1, 18),
    )

    assert resultado == ("series_territoriales_horarias_20260901T060000_20260901T180000")


def test_rechaza_intervalo_invertido() -> None:
    with pytest.raises(
        ValueError,
        match="fin debe ser posterior",
    ):
        _validar_parametros(
            inicio=datetime(2026, 9, 2),
            fin=datetime(2026, 9, 1),
            tamano_pagina=5000,
            timeout_segundos=120,
        )


def test_rechaza_tamano_pagina_invalido() -> None:
    with pytest.raises(
        ValueError,
        match="tamano_pagina debe ser mayor",
    ):
        _validar_parametros(
            inicio=datetime(2026, 9, 1),
            fin=datetime(2026, 9, 2),
            tamano_pagina=0,
            timeout_segundos=120,
        )


def test_rechaza_timeout_invalido() -> None:
    with pytest.raises(
        ValueError,
        match="timeout_segundos debe ser mayor",
    ):
        _validar_parametros(
            inicio=datetime(2026, 9, 1),
            fin=datetime(2026, 9, 2),
            tamano_pagina=5000,
            timeout_segundos=0,
        )
