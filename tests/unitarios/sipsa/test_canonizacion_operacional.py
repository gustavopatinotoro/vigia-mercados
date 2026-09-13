"""
Pruebas de canonización operacional SIPSA_P ↔ SIPSA_A.
"""

import pytest

from vigia.infraestructura.sipsa.canonizacion_operacional import (
    ErrorCanonizacionOperacionalSipsa,
    mercados_sipsa_p_soportados,
    normalizar_producto_sipsa,
    resolver_mercado_sipsa_p,
)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Aguacate*", "Aguacate"),
        ("Papa  criolla", "Papa criolla"),
        (" Piña * ", "Piña"),
        ("Tomate chonto", "Tomate chonto"),
        ("Mora de Castilla", "Mora de Castilla"),
    ],
)
def test_normaliza_producto_solo_editorialmente(
    entrada: str,
    esperado: str,
) -> None:
    assert normalizar_producto_sipsa(entrada) == esperado


@pytest.mark.parametrize(
    ("mercado_precio", "mercado_abastecimiento"),
    [
        (
            "CMA",
            "Medellín, Central Mayorista de Antioquia",
        ),
        (
            "Cenabastos",
            "Cúcuta, Cenabastos",
        ),
        (
            "Centroabastos",
            "Bucaramanga, Centroabastos",
        ),
        (
            "Corabastos",
            "Bogotá, D.C., Corabastos",
        ),
        (
            "La 21",
            "Ibagué, Plaza La 21",
        ),
        (
            "La 41-Impala",
            "Pereira, La 41-Impala",
        ),
        (
            "Mercar",
            "Armenia, Mercar",
        ),
        (
            "Santa Elena",
            "Cali, Santa Elena",
        ),
        (
            "Santa Marta",
            "Santa Marta (Magdalena)",
        ),
        (
            "Surabastos",
            "Neiva, Surabastos",
        ),
        (
            "Tunja",
            "Tunja, Complejo de Servicios del Sur",
        ),
    ],
)
def test_resuelve_mercados_por_catalogo_explicito(
    mercado_precio: str,
    mercado_abastecimiento: str,
) -> None:
    assert resolver_mercado_sipsa_p(mercado_precio) == mercado_abastecimiento


def test_rechaza_mercado_no_catalogado() -> None:
    with pytest.raises(
        ErrorCanonizacionOperacionalSipsa,
        match="No existe correspondencia explícita",
    ):
        resolver_mercado_sipsa_p("Mercado inventado")


@pytest.mark.parametrize(
    "valor",
    [
        "",
        " ",
        "*",
        "  *  ",
    ],
)
def test_rechaza_producto_vacio_tras_normalizacion(
    valor: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="producto SIPSA",
    ):
        normalizar_producto_sipsa(valor)


def test_catalogo_contiene_exactamente_los_once_mercados_validados() -> None:
    mercados = mercados_sipsa_p_soportados()

    assert len(mercados) == 11

    assert "Corabastos" in mercados
    assert "CMA" in mercados
    assert "Tunja" in mercados
