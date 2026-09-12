"""
Pruebas del contrato analítico de precios mensuales SIPSA.
"""

from datetime import date
from decimal import Decimal

import pytest

from vigia.dominio.sipsa import (
    ObservacionPrecioMensualSipsa,
)


def crear_observacion_valida(
    *,
    fecha_mes: date = date(2024, 1, 1),
    producto: str = "Acelga",
    mercado: str = "Bogotá, D.C., Corabastos",
    grupo: str = "VERDURAS Y HORTALIZAS",
    codigo_cpc: str | None = "0121903",
    precio_promedio_kg: Decimal = Decimal("1387"),
    fuente: str = "SIPSA-DANE",
    archivo_fuente: str = "mensual 24.csv",
) -> ObservacionPrecioMensualSipsa:
    """Construye una observación válida para pruebas."""
    return ObservacionPrecioMensualSipsa(
        fecha_mes=fecha_mes,
        producto=producto,
        mercado=mercado,
        grupo=grupo,
        codigo_cpc=codigo_cpc,
        precio_promedio_kg=precio_promedio_kg,
        fuente=fuente,
        archivo_fuente=archivo_fuente,
    )


def test_crea_observacion_mensual_valida() -> None:
    observacion = crear_observacion_valida()

    assert observacion.fecha_mes == date(2024, 1, 1)
    assert observacion.producto == "Acelga"
    assert observacion.codigo_cpc == "0121903"
    assert observacion.precio_promedio_kg == Decimal("1387")


def test_permite_codigo_cpc_ausente_en_periodo_historico() -> None:
    observacion = crear_observacion_valida(
        fecha_mes=date(2013, 1, 1),
        codigo_cpc=None,
        archivo_fuente="Mensual_2013_2017.csv",
    )

    assert observacion.codigo_cpc is None


def test_rechaza_fecha_que_no_sea_primer_dia_del_mes() -> None:
    with pytest.raises(
        ValueError,
        match="primer día del mes",
    ):
        crear_observacion_valida(
            fecha_mes=date(2024, 1, 15),
        )


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("producto", ""),
        ("producto", "   "),
        ("mercado", ""),
        ("grupo", ""),
        ("fuente", ""),
        ("archivo_fuente", ""),
    ],
)
def test_rechaza_textos_obligatorios_vacios(
    campo: str,
    valor: str,
) -> None:
    argumentos: dict[str, object] = {
        campo: valor,
    }

    with pytest.raises(ValueError):
        crear_observacion_valida(
            **argumentos,  # type: ignore[arg-type]
        )


def test_rechaza_codigo_cpc_vacio() -> None:
    with pytest.raises(
        ValueError,
        match="codigo_cpc",
    ):
        crear_observacion_valida(
            codigo_cpc="   ",
        )


@pytest.mark.parametrize(
    "precio",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("-0.01"),
    ],
)
def test_rechaza_precio_no_positivo(
    precio: Decimal,
) -> None:
    with pytest.raises(
        ValueError,
        match="mayor que cero",
    ):
        crear_observacion_valida(
            precio_promedio_kg=precio,
        )


def test_clave_natural_excluye_grupo_y_codigo_cpc() -> None:
    observacion = crear_observacion_valida()

    assert observacion.clave_natural == (
        date(2024, 1, 1),
        "Acelga",
        "Bogotá, D.C., Corabastos",
    )


def test_dos_observaciones_con_distinto_grupo_conservan_misma_clave() -> None:
    primera = crear_observacion_valida(
        fecha_mes=date(2013, 1, 1),
        producto="Arveja enlatada",
        grupo="GRANOS Y CEREALES",
        codigo_cpc=None,
    )

    segunda = crear_observacion_valida(
        fecha_mes=date(2013, 1, 1),
        producto="Arveja enlatada",
        grupo="PROCESADOS",
        codigo_cpc=None,
    )

    assert primera.clave_natural == segunda.clave_natural
