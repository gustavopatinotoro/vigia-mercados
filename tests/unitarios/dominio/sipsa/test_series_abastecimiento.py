"""
Pruebas del contrato canónico de abastecimiento diario SIPSA.
"""

from datetime import date
from decimal import Decimal

import pytest

from vigia.dominio.sipsa import (
    ObservacionAbastecimientoDiarioSipsa,
)


def _crear_observacion(
    *,
    cantidad_kg: Decimal = Decimal("78208"),
    numero_registros_fuente: int = 122,
) -> ObservacionAbastecimientoDiarioSipsa:
    return ObservacionAbastecimientoDiarioSipsa(
        fecha=date(2026, 5, 12),
        producto="Arveja verde en vaina",
        mercado_destino="Ipiales (Nariño), Centro de acopio",
        codigo_departamento_origen="52",
        codigo_municipio_pais_origen="52356",
        departamento_origen="Nariño",
        municipio_pais_origen="Ipiales",
        grupo="Verduras y hortalizas",
        codigo_cpc="01234",
        cantidad_kg=cantidad_kg,
        numero_registros_fuente=numero_registros_fuente,
        fuente="SIPSA-DANE",
        archivo_fuente="abastecimiento.xlsx",
    )


def test_construye_observacion_valida() -> None:
    observacion = _crear_observacion()

    assert observacion.cantidad_kg == Decimal("78208")
    assert observacion.numero_registros_fuente == 122


def test_clave_natural_no_incluye_cpc_ni_grupo() -> None:
    observacion = _crear_observacion()

    assert observacion.clave_natural == (
        date(2026, 5, 12),
        "Arveja verde en vaina",
        "Ipiales (Nariño), Centro de acopio",
        "52",
        "52356",
    )


@pytest.mark.parametrize(
    "cantidad",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_rechaza_cantidad_no_positiva(
    cantidad: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="cantidad_kg",
    ):
        _crear_observacion(
            cantidad_kg=cantidad,
        )


@pytest.mark.parametrize(
    "numero_registros",
    [
        0,
        -1,
    ],
)
def test_rechaza_numero_registros_no_positivo(
    numero_registros: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="numero_registros_fuente",
    ):
        _crear_observacion(
            numero_registros_fuente=numero_registros,
        )


def test_rechaza_campo_textual_vacio() -> None:
    with pytest.raises(
        ValueError,
        match="producto",
    ):
        ObservacionAbastecimientoDiarioSipsa(
            fecha=date(2026, 5, 12),
            producto=" ",
            mercado_destino="Mercado",
            codigo_departamento_origen="52",
            codigo_municipio_pais_origen="52356",
            departamento_origen="Nariño",
            municipio_pais_origen="Ipiales",
            grupo="Verduras",
            codigo_cpc="01234",
            cantidad_kg=Decimal("100"),
            numero_registros_fuente=1,
            fuente="SIPSA-DANE",
            archivo_fuente="fuente.xlsx",
        )
