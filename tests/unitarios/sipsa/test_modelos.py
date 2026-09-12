"""
Pruebas unitarias de los contratos canónicos SIPSA.
"""

from datetime import date
from decimal import Decimal

import pytest

from vigia.dominio.sipsa.modelos import (
    RegistroAbastecimiento,
    RegistroPrecioMayorista,
)


def test_crea_precio_mayorista_valido() -> None:
    """Acepta una observación válida de precio."""
    registro = RegistroPrecioMayorista(
        fecha=date(2026, 9, 1),
        producto="Ahuyama",
        categoria="Verduras y hortalizas",
        ciudad="Medellín",
        mercado="CMA",
        precio_kg=Decimal("1700"),
        variacion=Decimal("0.10"),
        fuente="SIPSA-DANE",
        archivo_fuente="anex-SIPSADiario-01sep2026.xlsx",
    )

    assert registro.precio_kg == Decimal("1700")
    assert registro.variacion == Decimal("0.10")


def test_precio_no_disponible_se_representa_con_none() -> None:
    """Permite ausencia explícita de precio sin convertirla en cero."""
    registro = RegistroPrecioMayorista(
        fecha=date(2026, 9, 1),
        producto="Ahuyama",
        categoria="Verduras y hortalizas",
        ciudad="Pereira",
        mercado="La 41-Impala",
        precio_kg=None,
        variacion=None,
        fuente="SIPSA-DANE",
        archivo_fuente="anex-SIPSADiario-01sep2026.xlsx",
    )

    assert registro.precio_kg is None
    assert registro.variacion is None


def test_rechaza_precio_negativo() -> None:
    """Impide precios físicamente inválidos."""
    with pytest.raises(ValueError, match="precio_kg no puede ser negativo"):
        RegistroPrecioMayorista(
            fecha=date(2026, 9, 1),
            producto="Ahuyama",
            categoria="Verduras y hortalizas",
            ciudad="Medellín",
            mercado="CMA",
            precio_kg=Decimal("-1"),
            variacion=None,
            fuente="SIPSA-DANE",
            archivo_fuente="archivo.xlsx",
        )


def test_crea_abastecimiento_valido() -> None:
    """Acepta un registro realista de abastecimiento."""
    registro = RegistroAbastecimiento(
        fecha=date(2026, 1, 2),
        ciudad_mercado="Armenia, Mercar",
        codigo_departamento_origen="52",
        codigo_municipio_pais_origen="52838",
        departamento_origen="NARIÑO",
        municipio_pais_origen="TÚQUERRES",
        grupo="TUBERCULOS, RAICES Y PLATANOS",
        codigo_cpc="0151001",
        producto="Papa capira",
        cantidad_kg=Decimal("8000"),
        fuente="SIPSA-DANE",
        archivo_fuente="anex-Microdato-abastecimiento-2026.xlsx",
        hoja_fuente="2.1",
    )

    assert registro.codigo_cpc == "0151001"
    assert registro.codigo_municipio_pais_origen == "52838"
    assert registro.cantidad_kg == Decimal("8000")


def test_rechaza_cantidad_negativa() -> None:
    """Impide cantidades de abastecimiento negativas."""
    with pytest.raises(ValueError, match="cantidad_kg no puede ser negativo"):
        RegistroAbastecimiento(
            fecha=date(2026, 1, 2),
            ciudad_mercado="Armenia, Mercar",
            codigo_departamento_origen="52",
            codigo_municipio_pais_origen="52838",
            departamento_origen="NARIÑO",
            municipio_pais_origen="TÚQUERRES",
            grupo="TUBERCULOS, RAICES Y PLATANOS",
            codigo_cpc="0151001",
            producto="Papa capira",
            cantidad_kg=Decimal("-100"),
            fuente="SIPSA-DANE",
            archivo_fuente="archivo.xlsx",
            hoja_fuente="2.1",
        )


def test_rechaza_producto_vacio() -> None:
    """Impide registros sin identidad textual del producto."""
    with pytest.raises(ValueError, match="producto no puede estar vacío"):
        RegistroPrecioMayorista(
            fecha=date(2026, 9, 1),
            producto="   ",
            categoria="Verduras y hortalizas",
            ciudad="Medellín",
            mercado="CMA",
            precio_kg=Decimal("1700"),
            variacion=None,
            fuente="SIPSA-DANE",
            archivo_fuente="archivo.xlsx",
        )
