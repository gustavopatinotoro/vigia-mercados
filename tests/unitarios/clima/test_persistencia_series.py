"""
Pruebas de persistencia de series climáticas territoriales.
"""

import csv
import gzip
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from vigia.dominio.clima import (
    ObservacionClimaticaTerritorialHoraria,
    VariableClimatica,
)
from vigia.infraestructura.clima import (
    persistir_series_territoriales_horarias,
)


def _observacion(
    *,
    codigo_divipola: str = "17001",
    variable: VariableClimatica = VariableClimatica.TEMPERATURA,
    fecha_hora: datetime = datetime(2026, 9, 1, 12),
    valor: str = "20.5",
    unidad: str = "°C",
    estaciones_utilizadas: int = 2,
    observaciones_fuente: int = 12,
) -> ObservacionClimaticaTerritorialHoraria:
    return ObservacionClimaticaTerritorialHoraria(
        codigo_divipola=codigo_divipola,
        variable=variable,
        fecha_hora=fecha_hora,
        valor=Decimal(valor),
        unidad=unidad,
        estaciones_utilizadas=estaciones_utilizadas,
        observaciones_fuente=observaciones_fuente,
    )


def test_persiste_csv_comprimido_y_manifiesto(
    tmp_path: Path,
) -> None:
    resultado = persistir_series_territoriales_horarias(
        [_observacion()],
        directorio=tmp_path,
        nombre_base="serie_prueba",
    )

    assert resultado.ruta_datos.exists()
    assert resultado.ruta_manifiesto.exists()
    assert resultado.registros == 1

    with gzip.open(
        resultado.ruta_datos,
        mode="rt",
        encoding="utf-8",
        newline="",
    ) as archivo:
        filas = list(csv.DictReader(archivo))

    assert len(filas) == 1
    assert filas[0]["codigo_divipola"] == "17001"
    assert filas[0]["variable"] == "temperatura"
    assert filas[0]["valor"] == "20.5"
    assert filas[0]["unidad"] == "°C"


def test_sha256_coincide_con_archivo_generado(
    tmp_path: Path,
) -> None:
    resultado = persistir_series_territoriales_horarias(
        [_observacion()],
        directorio=tmp_path,
        nombre_base="serie_prueba",
    )

    digest = hashlib.sha256(resultado.ruta_datos.read_bytes()).hexdigest()

    assert resultado.sha256 == digest


def test_manifiesto_conserva_metadatos(
    tmp_path: Path,
) -> None:
    observaciones = [
        _observacion(
            codigo_divipola="17001",
            fecha_hora=datetime(2026, 9, 1, 12),
        ),
        _observacion(
            codigo_divipola="17174",
            fecha_hora=datetime(2026, 9, 1, 13),
        ),
    ]

    resultado = persistir_series_territoriales_horarias(
        observaciones,
        directorio=tmp_path,
        nombre_base="serie_prueba",
    )

    manifiesto = json.loads(resultado.ruta_manifiesto.read_text(encoding="utf-8"))

    assert manifiesto["registros"] == 2
    assert manifiesto["territorios"] == 2
    assert manifiesto["variables"] == ["temperatura"]
    assert manifiesto["fecha_hora_minima"] == "2026-09-01T12:00:00"
    assert manifiesto["fecha_hora_maxima"] == "2026-09-01T13:00:00"
    assert manifiesto["sha256_datos"] == resultado.sha256


def test_orden_de_salida_es_determinista(
    tmp_path: Path,
) -> None:
    observaciones = [
        _observacion(
            codigo_divipola="17174",
            fecha_hora=datetime(2026, 9, 1, 13),
        ),
        _observacion(
            codigo_divipola="17001",
            fecha_hora=datetime(2026, 9, 1, 12),
        ),
    ]

    resultado = persistir_series_territoriales_horarias(
        observaciones,
        directorio=tmp_path,
        nombre_base="serie_prueba",
    )

    with gzip.open(
        resultado.ruta_datos,
        mode="rt",
        encoding="utf-8",
        newline="",
    ) as archivo:
        filas = list(csv.DictReader(archivo))

    assert filas[0]["codigo_divipola"] == "17001"
    assert filas[1]["codigo_divipola"] == "17174"


def test_gzip_es_reproducible_byte_a_byte(
    tmp_path: Path,
) -> None:
    observaciones = [
        _observacion(
            codigo_divipola="17001",
            fecha_hora=datetime(2026, 9, 1, 12),
        ),
        _observacion(
            codigo_divipola="17174",
            fecha_hora=datetime(2026, 9, 1, 13),
        ),
    ]

    resultado_a = persistir_series_territoriales_horarias(
        observaciones,
        directorio=tmp_path / "a",
        nombre_base="serie",
    )

    resultado_b = persistir_series_territoriales_horarias(
        reversed(observaciones),
        directorio=tmp_path / "b",
        nombre_base="serie",
    )

    assert resultado_a.ruta_datos.read_bytes() == resultado_b.ruta_datos.read_bytes()

    assert resultado_a.sha256 == resultado_b.sha256


def test_permite_serie_vacia(
    tmp_path: Path,
) -> None:
    resultado = persistir_series_territoriales_horarias(
        [],
        directorio=tmp_path,
        nombre_base="serie_vacia",
    )

    manifiesto = json.loads(resultado.ruta_manifiesto.read_text(encoding="utf-8"))

    assert resultado.registros == 0
    assert manifiesto["fecha_hora_minima"] is None
    assert manifiesto["fecha_hora_maxima"] is None


def test_rechaza_nombre_vacio(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="nombre_base no puede estar vacío",
    ):
        persistir_series_territoriales_horarias(
            [],
            directorio=tmp_path,
            nombre_base="",
        )
