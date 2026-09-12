"""
Pruebas de persistencia reproducible de precios mensuales SIPSA_P.
"""

from __future__ import annotations

import gzip
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from vigia.dominio.sipsa import (
    ObservacionPrecioMensualSipsa,
)
from vigia.infraestructura.sipsa.persistencia_precios_mensuales import (
    persistir_precios_mensuales_sipsa,
)


def _observacion(
    *,
    fecha_mes: date,
    producto: str,
    mercado: str,
    grupo: str,
    precio: str,
    codigo_cpc: str | None = None,
    archivo_fuente: str = "fuente.csv",
) -> ObservacionPrecioMensualSipsa:
    """Construye una observación válida para pruebas."""
    return ObservacionPrecioMensualSipsa(
        fecha_mes=fecha_mes,
        producto=producto,
        mercado=mercado,
        grupo=grupo,
        codigo_cpc=codigo_cpc,
        precio_promedio_kg=Decimal(precio),
        fuente="SIPSA-DANE",
        archivo_fuente=archivo_fuente,
    )


def _datos_prueba() -> list[ObservacionPrecioMensualSipsa]:
    """Genera datos que incluyen una clave conflictiva."""
    return [
        _observacion(
            fecha_mes=date(2024, 1, 1),
            producto="Acelga",
            mercado="Armenia, Mercar",
            grupo="VERDURAS Y HORTALIZAS",
            codigo_cpc="0121903",
            precio="1387",
            archivo_fuente="mensual 24.csv",
        ),
        _observacion(
            fecha_mes=date(2021, 11, 1),
            producto="Arveja enlatada",
            mercado=('Medellín, Plaza Minorista "José María Villa"'),
            grupo="Granos y Cereales",
            precio="8895",
            archivo_fuente="Mensual_2021.csv",
        ),
        _observacion(
            fecha_mes=date(2021, 11, 1),
            producto="Arveja enlatada",
            mercado=('Medellín, Plaza Minorista "José María Villa"'),
            grupo="Procesados",
            precio="8889",
            archivo_fuente="Mensual_2021.csv",
        ),
    ]


def test_persiste_observaciones_y_conflictos(
    tmp_path: Path,
) -> None:
    resultado = persistir_precios_mensuales_sipsa(
        _datos_prueba(),
        directorio=tmp_path,
    )

    assert resultado.observaciones == 3
    assert resultado.claves_candidatas == 2
    assert resultado.conflictos == 1
    assert resultado.observaciones_conflictivas == 2
    assert resultado.observaciones_excedentes == 1

    assert resultado.ruta_datos.exists()
    assert resultado.ruta_conflictos.exists()
    assert resultado.ruta_manifiesto.exists()


def test_archivo_principal_conserva_observaciones_conflictivas(
    tmp_path: Path,
) -> None:
    resultado = persistir_precios_mensuales_sipsa(
        _datos_prueba(),
        directorio=tmp_path,
    )

    with gzip.open(
        resultado.ruta_datos,
        mode="rt",
        encoding="utf-8",
    ) as archivo:
        lineas = archivo.readlines()

    assert len(lineas) == 4

    contenido = "".join(lineas)

    assert "8895" in contenido
    assert "8889" in contenido


def test_archivo_conflictos_contiene_solo_claves_repetidas(
    tmp_path: Path,
) -> None:
    resultado = persistir_precios_mensuales_sipsa(
        _datos_prueba(),
        directorio=tmp_path,
    )

    with gzip.open(
        resultado.ruta_conflictos,
        mode="rt",
        encoding="utf-8",
    ) as archivo:
        contenido = archivo.read()

    assert "Arveja enlatada" in contenido
    assert "8895" in contenido
    assert "8889" in contenido
    assert "Acelga" not in contenido


def test_manifiesto_refleja_metricas_y_hashes(
    tmp_path: Path,
) -> None:
    resultado = persistir_precios_mensuales_sipsa(
        _datos_prueba(),
        directorio=tmp_path,
    )

    manifiesto = json.loads(resultado.ruta_manifiesto.read_text(encoding="utf-8"))

    assert manifiesto["formato"] == "vigia-precios-mensuales-sipsa-v1"
    assert manifiesto["observaciones"] == 3
    assert manifiesto["claves_candidatas"] == 2
    assert manifiesto["conflictos"] == 1
    assert manifiesto["observaciones_conflictivas"] == 2
    assert manifiesto["observaciones_excedentes"] == 1
    assert manifiesto["fecha_minima"] == "2021-11-01"
    assert manifiesto["fecha_maxima"] == "2024-01-01"
    assert manifiesto["sha256_datos"] == resultado.sha256_datos
    assert manifiesto["sha256_conflictos"] == resultado.sha256_conflictos


def test_persistencia_es_reproducible_byte_a_byte(
    tmp_path: Path,
) -> None:
    observaciones = _datos_prueba()

    primera = persistir_precios_mensuales_sipsa(
        observaciones,
        directorio=tmp_path / "primera",
    )

    segunda = persistir_precios_mensuales_sipsa(
        list(reversed(observaciones)),
        directorio=tmp_path / "segunda",
    )

    assert primera.ruta_datos.read_bytes() == segunda.ruta_datos.read_bytes()

    assert primera.ruta_conflictos.read_bytes() == segunda.ruta_conflictos.read_bytes()

    assert primera.ruta_manifiesto.read_bytes() == segunda.ruta_manifiesto.read_bytes()

    assert primera.sha256_datos == segunda.sha256_datos

    assert primera.sha256_conflictos == segunda.sha256_conflictos


def test_sin_conflictos_genera_archivo_de_conflictos_vacio(
    tmp_path: Path,
) -> None:
    observaciones = [
        _observacion(
            fecha_mes=date(2024, 1, 1),
            producto="Acelga",
            mercado="Armenia, Mercar",
            grupo="VERDURAS Y HORTALIZAS",
            codigo_cpc="0121903",
            precio="1387",
        )
    ]

    resultado = persistir_precios_mensuales_sipsa(
        observaciones,
        directorio=tmp_path,
    )

    with gzip.open(
        resultado.ruta_conflictos,
        mode="rt",
        encoding="utf-8",
    ) as archivo:
        lineas = archivo.readlines()

    assert resultado.conflictos == 0
    assert resultado.observaciones_conflictivas == 0
    assert resultado.observaciones_excedentes == 0
    assert len(lineas) == 1


def test_rechaza_coleccion_vacia(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="al menos una observación",
    ):
        persistir_precios_mensuales_sipsa(
            [],
            directorio=tmp_path,
        )


@pytest.mark.parametrize(
    "nombre",
    [
        "",
        "   ",
        "../precios",
        "subdirectorio/precios",
    ],
)
def test_rechaza_nombre_invalido(
    tmp_path: Path,
    nombre: str,
) -> None:
    with pytest.raises(ValueError):
        persistir_precios_mensuales_sipsa(
            _datos_prueba(),
            directorio=tmp_path,
            nombre=nombre,
        )
