"""
Correspondencias operacionales explícitas entre productos SIPSA_P y SIPSA_A.

Este catálogo contiene únicamente asociaciones verificadas manualmente para
resolver diferencias de granularidad entre el boletín diario de precios
SIPSA_P y los microdatos de abastecimiento SIPSA_A.

No utiliza similitud textual, fuzzy matching ni inferencia semántica.

Una correspondencia puede representar:

- un alias explícito 1 -> 1;
- una familia comercial 1 -> N cuyos componentes de abastecimiento deben
  agregarse para compararse con el producto publicado en SIPSA_P.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from vigia.infraestructura.sipsa.canonizacion_operacional import (
    normalizar_producto_sipsa,
)


class TipoCorrespondenciaProducto(StrEnum):
    """Tipos de correspondencia operacional soportados."""

    ALIAS = "alias"
    FAMILIA = "familia"


@dataclass(frozen=True, slots=True)
class CorrespondenciaProductoSipsa:
    """Correspondencia explícita SIPSA_P -> uno o más productos SIPSA_A."""

    producto_precio: str
    productos_abastecimiento: tuple[str, ...]
    tipo: TipoCorrespondenciaProducto

    def __post_init__(self) -> None:
        producto_precio = normalizar_producto_sipsa(self.producto_precio)

        if producto_precio != self.producto_precio:
            raise ValueError("producto_precio debe almacenarse en forma canónica.")

        if not self.productos_abastecimiento:
            raise ValueError("productos_abastecimiento no puede estar vacío.")

        productos_normalizados = tuple(
            normalizar_producto_sipsa(producto) for producto in self.productos_abastecimiento
        )

        if productos_normalizados != self.productos_abastecimiento:
            raise ValueError("Los productos de abastecimiento deben almacenarse en forma canónica.")

        if len(set(self.productos_abastecimiento)) != len(self.productos_abastecimiento):
            raise ValueError("productos_abastecimiento contiene duplicados.")

        if (
            self.tipo is TipoCorrespondenciaProducto.ALIAS
            and len(self.productos_abastecimiento) != 1
        ):
            raise ValueError(
                "Una correspondencia de tipo alias debe contener "
                "exactamente un producto de abastecimiento."
            )

        if (
            self.tipo is TipoCorrespondenciaProducto.FAMILIA
            and len(self.productos_abastecimiento) < 2
        ):
            raise ValueError(
                "Una correspondencia de tipo familia debe contener "
                "al menos dos productos de abastecimiento."
            )


CORRESPONDENCIAS_PRODUCTOS_SIPSA: tuple[
    CorrespondenciaProductoSipsa,
    ...,
] = (
    CorrespondenciaProductoSipsa(
        producto_precio="Aguacate",
        productos_abastecimiento=(
            "Aguacate Choquette",
            "Aguacate Hass",
            "Aguacate común",
            "Aguacate papelillo",
            "Aguacates otros",
        ),
        tipo=TipoCorrespondenciaProducto.FAMILIA,
    ),
    CorrespondenciaProductoSipsa(
        producto_precio="Banano",
        productos_abastecimiento=(
            "Banano Urabá",
            "Banano bocadillo",
            "Banano criollo",
        ),
        tipo=TipoCorrespondenciaProducto.FAMILIA,
    ),
    CorrespondenciaProductoSipsa(
        producto_precio="Guayaba",
        productos_abastecimiento=(
            "Guayaba común",
            "Guayaba pera",
            "Guayabas otras",
        ),
        tipo=TipoCorrespondenciaProducto.FAMILIA,
    ),
    CorrespondenciaProductoSipsa(
        producto_precio="Mandarina",
        productos_abastecimiento=(
            "Mandarina Arrayana",
            "Mandarina Oneco",
            "Mandarina común",
            "Mandarinas otras",
        ),
        tipo=TipoCorrespondenciaProducto.FAMILIA,
    ),
    CorrespondenciaProductoSipsa(
        producto_precio="Mora de Castilla",
        productos_abastecimiento=("Mora",),
        tipo=TipoCorrespondenciaProducto.ALIAS,
    ),
    CorrespondenciaProductoSipsa(
        producto_precio="Naranja",
        productos_abastecimiento=(
            "Naranja Valencia y/o Sweet",
            "Naranja común",
            "Naranjas otras",
        ),
        tipo=TipoCorrespondenciaProducto.FAMILIA,
    ),
    CorrespondenciaProductoSipsa(
        producto_precio="Piña",
        productos_abastecimiento=(
            "Piña gold",
            "Piña perolera",
            "Piñas otras",
        ),
        tipo=TipoCorrespondenciaProducto.FAMILIA,
    ),
)


_CORRESPONDENCIA_POR_PRODUCTO: dict[
    str,
    CorrespondenciaProductoSipsa,
] = {
    correspondencia.producto_precio: correspondencia
    for correspondencia in CORRESPONDENCIAS_PRODUCTOS_SIPSA
}


def obtener_correspondencia_producto(
    producto_precio: str,
) -> CorrespondenciaProductoSipsa | None:
    """
    Obtiene una correspondencia explícita para un producto SIPSA_P.

    Retorna None cuando no existe una decisión auditada.
    """
    producto = normalizar_producto_sipsa(producto_precio)

    return _CORRESPONDENCIA_POR_PRODUCTO.get(producto)


def productos_abastecimiento_equivalentes(
    producto_precio: str,
) -> tuple[str, ...] | None:
    """Devuelve los productos SIPSA_A asociados explícitamente a SIPSA_P."""
    correspondencia = obtener_correspondencia_producto(producto_precio)

    if correspondencia is None:
        return None

    return correspondencia.productos_abastecimiento
