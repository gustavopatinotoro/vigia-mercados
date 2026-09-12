"""
Pruebas de los parsers históricos mensuales SIPSA_P.
"""

from datetime import date
from decimal import Decimal

import pytest

from vigia.infraestructura.sipsa import (
    ErrorParserPreciosMensualesLegadoSipsa,
    ErrorParserPreciosMensualesModernoSipsa,
    parsear_precios_mensuales_legado_sipsa,
    parsear_precios_mensuales_moderno_sipsa,
)


def test_parsea_registro_legado() -> None:
    contenido = (
        "Fecha;Grupo;Producto;Fuente;Precio\r\n"
        "1/01/2013;CARNES;Alas de pollo con costillar;"
        "Barranquilla, Barranquillita;3073\r\n"
    ).encode("latin-1")

    registros = list(
        parsear_precios_mensuales_legado_sipsa(
            contenido,
            archivo_fuente="Mensual_2013_2017.csv",
        )
    )

    assert len(registros) == 1

    registro = registros[0]

    assert registro.fecha_mes == date(2013, 1, 1)
    assert registro.producto == "Alas de pollo con costillar"
    assert registro.mercado == "Barranquilla, Barranquillita"
    assert registro.grupo == "CARNES"
    assert registro.codigo_cpc is None
    assert registro.precio_promedio_kg == Decimal("3073")


def test_normaliza_dia_de_fecha_legada_al_primer_dia_del_mes() -> None:
    contenido = (
        "Fecha;Grupo;Producto;Fuente;Precio\r\n"
        "15/02/2014;CARNES;Producto prueba;"
        "Mercado prueba;2500\r\n"
    ).encode("latin-1")

    registro = next(
        parsear_precios_mensuales_legado_sipsa(
            contenido,
            archivo_fuente="legado.csv",
        )
    )

    assert registro.fecha_mes == date(2014, 2, 1)


def test_parsea_caracteres_latin1_del_esquema_legado() -> None:
    contenido = (
        "Fecha;Grupo;Producto;Fuente;Precio\r\n"
        "1/01/2013;CARNES;Producto prueba;"
        '"Medellín, Plaza Minorista ""José María Villa""";3717\r\n'
    ).encode("latin-1")

    registro = next(
        parsear_precios_mensuales_legado_sipsa(
            contenido,
            archivo_fuente="legado.csv",
        )
    )

    assert registro.mercado == 'Medellín, Plaza Minorista "José María Villa"'


def test_rechaza_encabezado_legado_desconocido() -> None:
    contenido = ("Fecha;Producto;Precio\r\n1/01/2013;Acelga;1000\r\n").encode("latin-1")

    with pytest.raises(
        ErrorParserPreciosMensualesLegadoSipsa,
        match="Encabezado",
    ):
        list(
            parsear_precios_mensuales_legado_sipsa(
                contenido,
                archivo_fuente="legado.csv",
            )
        )


def test_rechaza_precio_legado_invalido() -> None:
    contenido = (
        "Fecha;Grupo;Producto;Fuente;Precio\r\n1/01/2013;CARNES;Producto;Mercado;abc\r\n"
    ).encode("latin-1")

    with pytest.raises(
        ErrorParserPreciosMensualesLegadoSipsa,
        match="Precio inválido",
    ):
        list(
            parsear_precios_mensuales_legado_sipsa(
                contenido,
                archivo_fuente="legado.csv",
            )
        )


def test_parsea_registro_moderno() -> None:
    contenido = (
        "\ufeffFecha;Grupo;Producto;CODIGO_CPC_AC;"
        "Mercado;Precio promedio por kilogramo*\r\n"
        "ene-24;VERDURAS Y HORTALIZAS;Acelga;0121903;"
        "Armenia, Mercar;1.387\r\n"
    ).encode()

    registros = list(
        parsear_precios_mensuales_moderno_sipsa(
            contenido,
            archivo_fuente="mensual 24.csv",
        )
    )

    assert len(registros) == 1

    registro = registros[0]

    assert registro.fecha_mes == date(2024, 1, 1)
    assert registro.producto == "Acelga"
    assert registro.mercado == "Armenia, Mercar"
    assert registro.grupo == "VERDURAS Y HORTALIZAS"
    assert registro.codigo_cpc == "0121903"
    assert registro.precio_promedio_kg == Decimal("1387")


def test_parsea_precio_moderno_sin_separador_de_miles() -> None:
    contenido = (
        "Fecha;Grupo;Producto;CODIGO_CPC_AC;"
        "Mercado;Precio promedio por kilogramo*\r\n"
        "ene-24;VERDURAS Y HORTALIZAS;Acelga;0121903;"
        "Bogotá, D.C., Corabastos;607\r\n"
    ).encode()

    registro = next(
        parsear_precios_mensuales_moderno_sipsa(
            contenido,
            archivo_fuente="moderno.csv",
        )
    )

    assert registro.precio_promedio_kg == Decimal("607")


@pytest.mark.parametrize(
    "precio",
    [
        "1,387",
        "1.38",
        "1.387,50",
        "abc",
    ],
)
def test_rechaza_formatos_de_precio_moderno_no_observados(
    precio: str,
) -> None:
    contenido = (
        "Fecha;Grupo;Producto;CODIGO_CPC_AC;"
        "Mercado;Precio promedio por kilogramo*\r\n"
        f"ene-24;GRUPO;Producto;0123456;Mercado;{precio}\r\n"
    ).encode()

    with pytest.raises(
        ErrorParserPreciosMensualesModernoSipsa,
        match="Formato de precio inválido",
    ):
        list(
            parsear_precios_mensuales_moderno_sipsa(
                contenido,
                archivo_fuente="moderno.csv",
            )
        )


def test_rechaza_mes_moderno_desconocido() -> None:
    contenido = (
        b"Fecha;Grupo;Producto;CODIGO_CPC_AC;"
        b"Mercado;Precio promedio por kilogramo*\r\n"
        b"xyz-24;GRUPO;Producto;0123456;Mercado;1.000\r\n"
    )

    with pytest.raises(
        ErrorParserPreciosMensualesModernoSipsa,
        match="Mes inválido",
    ):
        list(
            parsear_precios_mensuales_moderno_sipsa(
                contenido,
                archivo_fuente="moderno.csv",
            )
        )


def test_rechaza_encabezado_moderno_desconocido() -> None:
    contenido = b"Fecha;Producto;Precio\r\nene-24;Acelga;1.000\r\n"

    with pytest.raises(
        ErrorParserPreciosMensualesModernoSipsa,
        match="Encabezado",
    ):
        list(
            parsear_precios_mensuales_moderno_sipsa(
                contenido,
                archivo_fuente="moderno.csv",
            )
        )
