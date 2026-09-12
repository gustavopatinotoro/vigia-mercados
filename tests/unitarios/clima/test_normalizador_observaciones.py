"""
Pruebas de normalización de observaciones IDEAM.
"""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal

import pytest

from vigia.dominio.clima import (
    ObservacionClimatica,
    VariableClimatica,
)
from vigia.infraestructura.ideam.normalizador_observaciones import (
    ErrorConflictoObservacionIdeam,
    normalizar_observaciones_ideam,
)


def _observacion() -> ObservacionClimatica:
    """Construye una observación climática válida."""
    return ObservacionClimatica(
        codigo_estacion="0026155110",
        codigo_sensor="0068",
        fecha=datetime.fromisoformat("2026-07-24T23:00:00"),
        variable=VariableClimatica.TEMPERATURA,
        valor=Decimal("19.4"),
        unidad="°C",
        nombre_estacion="AEROPUERTO LA NUBIA",
        departamento="CALDAS",
        municipio="MANIZALES",
        latitud=Decimal("5.029"),
        longitud=Decimal("-75.464"),
        descripcion_sensor="TEMPERATURA DEL AIRE A 2 m",
    )


def test_elimina_duplicados_exactos() -> None:
    """Conserva una sola observación cuando todas son idénticas."""
    observacion = _observacion()

    resultado = normalizar_observaciones_ideam(
        [
            observacion,
            observacion,
            observacion,
        ]
    )

    assert len(resultado.observaciones) == 1
    assert resultado.duplicados_eliminados == 2


def test_conserva_observaciones_temporales_distintas() -> None:
    """No mezcla observaciones realizadas en instantes diferentes."""
    primera = _observacion()

    segunda = replace(
        primera,
        fecha=datetime.fromisoformat("2026-07-24T22:00:00"),
        valor=Decimal("21.9"),
    )

    resultado = normalizar_observaciones_ideam(
        [
            primera,
            segunda,
        ]
    )

    assert len(resultado.observaciones) == 2
    assert resultado.duplicados_eliminados == 0


def test_detecta_valores_conflictivos() -> None:
    """Rechaza valores distintos para la misma estación, sensor y fecha."""
    primera = _observacion()

    segunda = replace(
        primera,
        valor=Decimal("20.0"),
    )

    with pytest.raises(
        ErrorConflictoObservacionIdeam,
        match="contradictorias",
    ):
        normalizar_observaciones_ideam(
            [
                primera,
                segunda,
            ]
        )


def test_entrada_vacia() -> None:
    """Permite normalizar una colección sin observaciones."""
    resultado = normalizar_observaciones_ideam([])

    assert resultado.observaciones == ()
    assert resultado.duplicados_eliminados == 0
