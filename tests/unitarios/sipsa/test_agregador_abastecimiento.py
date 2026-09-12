"""
Pruebas del agregador diario SIPSA_A.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from vigia.dominio.sipsa import RegistroAbastecimiento
from vigia.infraestructura.sipsa.agregador_abastecimiento import (
    ErrorAgregacionAbastecimientoSipsa,
    agregar_abastecimiento_diario_sipsa,
    eliminar_base_temporal_abastecimiento,
)


def _registro(
    *,
    cantidad: str,
    producto: str = "Arveja verde en vaina",
    codigo_cpc: str = "01234",
    grupo: str = "Verduras y hortalizas",
    departamento: str = "Nariño",
    municipio: str = "Ipiales",
) -> RegistroAbastecimiento:
    return RegistroAbastecimiento(
        fecha=date(2026, 5, 12),
        ciudad_mercado="Ipiales (Nariño), Centro de acopio",
        codigo_departamento_origen="52",
        codigo_municipio_pais_origen="52356",
        departamento_origen=departamento,
        municipio_pais_origen=municipio,
        grupo=grupo,
        codigo_cpc=codigo_cpc,
        producto=producto,
        cantidad_kg=Decimal(cantidad),
        fuente="SIPSA-DANE",
        archivo_fuente="abastecimiento.xlsx",
        hoja_fuente="2.2",
    )


def test_agrega_cantidades_de_la_misma_clave(
    tmp_path: Path,
) -> None:
    registros = [
        _registro(cantidad="52"),
        _registro(cantidad="312"),
        _registro(cantidad="1560"),
    ]

    resultado = list(
        agregar_abastecimiento_diario_sipsa(
            registros,
            ruta_bd_temporal=tmp_path / "agregacion.sqlite",
        )
    )

    assert len(resultado) == 1

    observacion = resultado[0]

    assert observacion.cantidad_kg == Decimal("1924")
    assert observacion.numero_registros_fuente == 3


def test_preserva_repeticiones_exactas_como_aportes(
    tmp_path: Path,
) -> None:
    registros = [
        _registro(cantidad="312"),
        _registro(cantidad="312"),
        _registro(cantidad="312"),
    ]

    resultado = list(
        agregar_abastecimiento_diario_sipsa(
            registros,
            ruta_bd_temporal=tmp_path / "agregacion.sqlite",
        )
    )

    assert resultado[0].cantidad_kg == Decimal("936")
    assert resultado[0].numero_registros_fuente == 3


def test_suma_decimal_sin_perdida_binaria(
    tmp_path: Path,
) -> None:
    registros = [
        _registro(cantidad="0.1"),
        _registro(cantidad="0.2"),
    ]

    resultado = list(
        agregar_abastecimiento_diario_sipsa(
            registros,
            ruta_bd_temporal=tmp_path / "agregacion.sqlite",
        )
    )

    assert resultado[0].cantidad_kg == Decimal("0.3")


def test_separa_claves_distintas(
    tmp_path: Path,
) -> None:
    registros = [
        _registro(
            cantidad="100",
            producto="Arveja verde en vaina",
        ),
        _registro(
            cantidad="200",
            producto="Zanahoria",
        ),
    ]

    resultado = list(
        agregar_abastecimiento_diario_sipsa(
            registros,
            ruta_bd_temporal=tmp_path / "agregacion.sqlite",
        )
    )

    assert len(resultado) == 2


@pytest.mark.parametrize(
    (
        "campo",
        "valor",
    ),
    [
        ("codigo_cpc", "99999"),
        ("grupo", "Otro grupo"),
        ("departamento", "Caldas"),
        ("municipio", "Pasto"),
    ],
)
def test_rechaza_atributos_contradictorios_en_misma_clave(
    tmp_path: Path,
    campo: str,
    valor: str,
) -> None:
    argumentos = {
        "cantidad": "200",
    }

    argumentos[campo] = valor

    segundo = _registro(
        **argumentos,
    )

    registros = [
        _registro(cantidad="100"),
        segundo,
    ]

    with pytest.raises(
        ErrorAgregacionAbastecimientoSipsa,
        match="atributos contradictorios",
    ):
        list(
            agregar_abastecimiento_diario_sipsa(
                registros,
                ruta_bd_temporal=tmp_path / "agregacion.sqlite",
            )
        )


def test_rechaza_fuente_vacia(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ErrorAgregacionAbastecimientoSipsa,
        match="No se recibieron",
    ):
        list(
            agregar_abastecimiento_diario_sipsa(
                [],
                ruta_bd_temporal=tmp_path / "agregacion.sqlite",
            )
        )


def test_rechaza_intervalo_confirmacion_invalido(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="confirmar_cada",
    ):
        list(
            agregar_abastecimiento_diario_sipsa(
                [_registro(cantidad="100")],
                ruta_bd_temporal=tmp_path / "agregacion.sqlite",
                confirmar_cada=0,
            )
        )


def test_elimina_base_temporal(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / "agregacion.sqlite"

    list(
        agregar_abastecimiento_diario_sipsa(
            [_registro(cantidad="100")],
            ruta_bd_temporal=ruta,
        )
    )

    assert ruta.exists()

    eliminar_base_temporal_abastecimiento(ruta)

    assert not ruta.exists()
