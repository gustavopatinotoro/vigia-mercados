"""
Pruebas del catálogo operacional de correspondencias de productos SIPSA.
"""

import pytest

from vigia.infraestructura.sipsa.correspondencias_productos import (
    CORRESPONDENCIAS_PRODUCTOS_SIPSA,
    CorrespondenciaProductoSipsa,
    TipoCorrespondenciaProducto,
    obtener_correspondencia_producto,
    productos_abastecimiento_equivalentes,
)


def test_catalogo_contiene_siete_correspondencias_auditadas() -> None:
    assert len(CORRESPONDENCIAS_PRODUCTOS_SIPSA) == 7


@pytest.mark.parametrize(
    "producto",
    [
        "Aguacate",
        "Banano",
        "Guayaba",
        "Mandarina",
        "Naranja",
        "Piña",
    ],
)
def test_correspondencias_de_familia(
    producto: str,
) -> None:
    correspondencia = obtener_correspondencia_producto(producto)

    assert correspondencia is not None
    assert correspondencia.tipo is TipoCorrespondenciaProducto.FAMILIA
    assert len(correspondencia.productos_abastecimiento) >= 2


def test_mora_de_castilla_es_alias_explicito() -> None:
    correspondencia = obtener_correspondencia_producto("Mora de Castilla")

    assert correspondencia is not None
    assert correspondencia.tipo is TipoCorrespondenciaProducto.ALIAS
    assert correspondencia.productos_abastecimiento == ("Mora",)


def test_familia_aguacate_contiene_variedades_auditadas() -> None:
    productos = productos_abastecimiento_equivalentes("Aguacate")

    assert productos == (
        "Aguacate Choquette",
        "Aguacate Hass",
        "Aguacate común",
        "Aguacate papelillo",
        "Aguacates otros",
    )


def test_tomate_permanece_sin_correspondencia() -> None:
    assert obtener_correspondencia_producto("Tomate") is None


def test_tomate_de_arbol_no_puede_entrar_por_accidente() -> None:
    for correspondencia in CORRESPONDENCIAS_PRODUCTOS_SIPSA:
        if correspondencia.producto_precio == "Tomate":
            pytest.fail("Tomate no debe tener correspondencia operacional.")

        assert "Tomate de árbol" not in correspondencia.productos_abastecimiento


@pytest.mark.parametrize(
    "producto",
    [
        "Manzana royal gala",
        "Papa negra",
        "Tomate",
    ],
)
def test_productos_no_resueltos_permanecen_no_resueltos(
    producto: str,
) -> None:
    assert obtener_correspondencia_producto(producto) is None


def test_busqueda_tolera_ruido_editorial_conocido() -> None:
    correspondencia = obtener_correspondencia_producto("  Aguacate* ")

    assert correspondencia is not None
    assert correspondencia.producto_precio == "Aguacate"


def test_rechaza_alias_con_multiples_destinos() -> None:
    with pytest.raises(
        ValueError,
        match="exactamente un producto",
    ):
        CorrespondenciaProductoSipsa(
            producto_precio="Prueba",
            productos_abastecimiento=(
                "Producto A",
                "Producto B",
            ),
            tipo=TipoCorrespondenciaProducto.ALIAS,
        )


def test_rechaza_familia_con_un_solo_destino() -> None:
    with pytest.raises(
        ValueError,
        match="al menos dos productos",
    ):
        CorrespondenciaProductoSipsa(
            producto_precio="Prueba",
            productos_abastecimiento=("Producto A",),
            tipo=TipoCorrespondenciaProducto.FAMILIA,
        )


def test_rechaza_destinos_duplicados() -> None:
    with pytest.raises(
        ValueError,
        match="duplicados",
    ):
        CorrespondenciaProductoSipsa(
            producto_precio="Prueba",
            productos_abastecimiento=(
                "Producto A",
                "Producto A",
            ),
            tipo=TipoCorrespondenciaProducto.FAMILIA,
        )
