"""
Pruebas de persistencia reproducible de abastecimiento SIPSA_A.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from vigia.dominio.sipsa import (
    ObservacionAbastecimientoDiarioSipsa,
)
from vigia.infraestructura.sipsa.persistencia_abastecimiento import (
    ErrorPersistenciaAbastecimientoSipsa,
    persistir_abastecimiento_diario_sipsa,
)


def _observacion(
    *,
    fecha: date,
    producto: str,
    cantidad: str,
    registros_fuente: int = 1,
) -> ObservacionAbastecimientoDiarioSipsa:
    return ObservacionAbastecimientoDiarioSipsa(
        fecha=fecha,
        producto=producto,
        mercado_destino="Mercado",
        codigo_departamento_origen="17",
        codigo_municipio_pais_origen="17001",
        departamento_origen="Caldas",
        municipio_pais_origen="Manizales",
        grupo="Grupo",
        codigo_cpc="01234",
        cantidad_kg=Decimal(cantidad),
        numero_registros_fuente=registros_fuente,
        fuente="SIPSA-DANE",
        archivo_fuente="abastecimiento.xlsx",
    )


def test_persiste_estadisticas(
    tmp_path: Path,
) -> None:
    observaciones = [
        _observacion(
            fecha=date(2026, 1, 2),
            producto="Papa",
            cantidad="100.25",
            registros_fuente=2,
        ),
        _observacion(
            fecha=date(2026, 1, 3),
            producto="Yuca",
            cantidad="200.75",
            registros_fuente=3,
        ),
    ]

    resultado = persistir_abastecimiento_diario_sipsa(
        observaciones,
        directorio=tmp_path,
    )

    assert resultado.observaciones == 2
    assert resultado.registros_fuente == 5
    assert resultado.cantidad_total_kg == Decimal("301.00")
    assert resultado.fecha_minima == "2026-01-02"
    assert resultado.fecha_maxima == "2026-01-03"

    assert resultado.ruta_datos.exists()
    assert resultado.ruta_manifiesto.exists()


def test_es_reproducible_independiente_del_orden(
    tmp_path: Path,
) -> None:
    observaciones = [
        _observacion(
            fecha=date(2026, 1, 3),
            producto="Yuca",
            cantidad="200",
        ),
        _observacion(
            fecha=date(2026, 1, 2),
            producto="Papa",
            cantidad="100",
        ),
    ]

    resultado_a = persistir_abastecimiento_diario_sipsa(
        observaciones,
        directorio=tmp_path / "a",
    )

    resultado_b = persistir_abastecimiento_diario_sipsa(
        reversed(observaciones),
        directorio=tmp_path / "b",
    )

    assert resultado_a.ruta_datos.read_bytes() == resultado_b.ruta_datos.read_bytes()

    assert resultado_a.ruta_manifiesto.read_bytes() == resultado_b.ruta_manifiesto.read_bytes()

    assert resultado_a.sha256_datos == resultado_b.sha256_datos


def test_rechaza_clave_duplicada(
    tmp_path: Path,
) -> None:
    observacion = _observacion(
        fecha=date(2026, 1, 2),
        producto="Papa",
        cantidad="100",
    )

    with pytest.raises(
        ErrorPersistenciaAbastecimientoSipsa,
        match="clave analítica duplicada",
    ):
        persistir_abastecimiento_diario_sipsa(
            [
                observacion,
                observacion,
            ],
            directorio=tmp_path,
        )


def test_rechaza_fuente_vacia(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ErrorPersistenciaAbastecimientoSipsa,
        match="No se recibieron",
    ):
        persistir_abastecimiento_diario_sipsa(
            [],
            directorio=tmp_path,
        )


@pytest.mark.parametrize(
    "nombre",
    [
        "",
        ".",
        "..",
        "../salida",
        "carpeta/salida",
    ],
)
def test_rechaza_nombre_invalido(
    tmp_path: Path,
    nombre: str,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        persistir_abastecimiento_diario_sipsa(
            [
                _observacion(
                    fecha=date(2026, 1, 2),
                    producto="Papa",
                    cantidad="100",
                )
            ],
            directorio=tmp_path,
            nombre=nombre,
        )
