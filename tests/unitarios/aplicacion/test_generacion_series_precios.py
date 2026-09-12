"""
Pruebas del caso de uso de generación histórica SIPSA_P.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from vigia.aplicacion.series_precios import (
    ErrorGeneracionPreciosMensuales,
    generar_serie_historica_precios_sipsa,
)


def _crear_zip(
    ruta: Path,
    *,
    nombre_csv: str,
    contenido: bytes,
) -> None:
    """Crea una fuente ZIP SIPSA_P mínima para pruebas."""
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        ruta,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archivo_zip:
        archivo_zip.writestr(
            nombre_csv,
            contenido,
        )


def _crear_fuentes_completas(
    directorio: Path,
) -> None:
    """Crea una colección mínima que cubre todos los perfiles históricos."""
    legado = (
        "Fecha;Grupo;Producto;Fuente;Precio\r\n"
        "1/01/2013;CARNES;Producto legado;"
        "Mercado legado;1000\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2013_2017.zip",
        nombre_csv="Mensual_2013_2017.csv",
        contenido=legado,
    )

    legado_2018 = (
        "Fecha;Grupo;Producto;Fuente;Precio\r\n1/01/2018;CARNES;Producto 2018;Mercado 2018;1100\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2018.zip",
        nombre_csv="Mensual_2018.csv",
        contenido=legado_2018,
    )

    intermedio_2019 = (
        "Fecha;Grupo;Producto;Fuente;Precio_por_kilogramo\r\n"
        "1/01/2019;CARNES;Producto 2019;"
        "Mercado 2019;1200\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2019.zip",
        nombre_csv="Mensual_2019.csv",
        contenido=intermedio_2019,
    )

    intermedio_2020 = (
        "Fecha;Grupo;Producto;Mercado;Precio_por_kilogramo\r\n"
        "1/01/2020;CARNES;Producto 2020;"
        "Mercado 2020;1300\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2020.zip",
        nombre_csv="Mensual_2020.csv",
        contenido=intermedio_2020,
    )

    intermedio_2021 = (
        "Fecha;Grupo;Producto;Mercado;"
        "Precio_promedio_por_kilogramo\r\n"
        "1/01/2021;CARNES;Producto 2021;"
        "Mercado 2021;1400\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2021.zip",
        nombre_csv="Mensual_2021.csv",
        contenido=intermedio_2021,
    )

    abreviado_2022 = (
        "Fecha;Grupo;Producto;Mercado;"
        "Precio promedio por kilogramo*;;\r\n"
        "ene-22;CARNES;Producto 2022;"
        "Mercado 2022;1.500;;\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2022.zip",
        nombre_csv="mensual 22.csv",
        contenido=abreviado_2022,
    )

    abreviado_2023 = (
        "Fecha;Grupo;Producto;Mercado;"
        "Precio promedio por kilogramo*;\r\n"
        "ene-23;CARNES;Producto 2023;"
        "Mercado 2023;1.600;\r\n"
    ).encode("latin-1")

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2023.zip",
        nombre_csv="mensual 23.csv",
        contenido=abreviado_2023,
    )

    moderno_2024 = (
        "\ufeffFecha;Grupo;Producto;CODIGO_CPC_AC;"
        "Mercado;Precio promedio por kilogramo*\r\n"
        "ene-24;CARNES;Producto 2024;0299999;"
        "Mercado 2024;1.700\r\n"
    ).encode()

    _crear_zip(
        directorio / "BaseDatos-SIPSA_P-Mensual-2024.zip",
        nombre_csv="mensual 24.csv",
        contenido=moderno_2024,
    )


def test_genera_serie_historica_con_todos_los_perfiles(
    tmp_path: Path,
) -> None:
    fuentes = tmp_path / "fuentes"
    salida = tmp_path / "salida"

    _crear_fuentes_completas(fuentes)

    resultado = generar_serie_historica_precios_sipsa(
        directorio_fuentes=fuentes,
        directorio_salida=salida,
    )

    assert resultado.observaciones == 8
    assert resultado.claves_candidatas == 8
    assert resultado.conflictos == 0
    assert resultado.observaciones_conflictivas == 0
    assert resultado.observaciones_excedentes == 0

    perfiles = [estadistica.perfil for estadistica in resultado.estadisticas_archivos]

    assert perfiles == [
        "2013-2018",
        "2013-2018",
        "2019",
        "2020",
        "2021",
        "2022-2023",
        "2022-2023",
        "2024",
    ]

    assert resultado.persistencia.ruta_datos.exists()
    assert resultado.persistencia.ruta_conflictos.exists()
    assert resultado.persistencia.ruta_manifiesto.exists()


def test_falla_si_falta_un_anio(
    tmp_path: Path,
) -> None:
    fuentes = tmp_path / "fuentes"

    _crear_fuentes_completas(fuentes)

    (fuentes / "BaseDatos-SIPSA_P-Mensual-2020.zip").unlink()

    with pytest.raises(
        ErrorGeneracionPreciosMensuales,
        match="2020",
    ):
        generar_serie_historica_precios_sipsa(
            directorio_fuentes=fuentes,
            directorio_salida=tmp_path / "salida",
        )


def test_falla_si_hay_multiples_zip_para_un_anio(
    tmp_path: Path,
) -> None:
    fuentes = tmp_path / "fuentes"

    _crear_fuentes_completas(fuentes)

    _crear_zip(
        fuentes / "BaseDatos-SIPSA_P-Mensual-2019-copia.zip",
        nombre_csv="Mensual_2019.csv",
        contenido=(
            "Fecha;Grupo;Producto;Fuente;"
            "Precio_por_kilogramo\r\n"
            "1/01/2019;CARNES;Producto;"
            "Mercado;1000\r\n"
        ).encode("latin-1"),
    )

    with pytest.raises(
        ErrorGeneracionPreciosMensuales,
        match="2019",
    ):
        generar_serie_historica_precios_sipsa(
            directorio_fuentes=fuentes,
            directorio_salida=tmp_path / "salida",
        )


def test_falla_si_zip_contiene_multiples_csv(
    tmp_path: Path,
) -> None:
    fuentes = tmp_path / "fuentes"

    _crear_fuentes_completas(fuentes)

    ruta = fuentes / "BaseDatos-SIPSA_P-Mensual-2020.zip"

    with zipfile.ZipFile(
        ruta,
        mode="a",
    ) as archivo_zip:
        archivo_zip.writestr(
            "otro.csv",
            b"campo\r\nvalor\r\n",
        )

    with pytest.raises(
        ErrorGeneracionPreciosMensuales,
        match="exactamente un CSV",
    ):
        generar_serie_historica_precios_sipsa(
            directorio_fuentes=fuentes,
            directorio_salida=tmp_path / "salida",
        )
