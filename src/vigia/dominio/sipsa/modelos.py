"""
Modelos canónicos del dominio SIPSA.

Los modelos definidos aquí representan información ya validada y normalizada.
No contienen conocimiento sobre hojas, filas, columnas ni formatos Excel.

Reglas principales:
- Los códigos geográficos y CPC se mantienen como texto.
- Los precios y cantidades no pueden ser negativos.
- Un precio no disponible se representa con ``None``, nunca con cero.
- Los registros conservan información de trazabilidad de su fuente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


def _validar_texto(valor: str, campo: str) -> None:
    """Valida que un campo textual obligatorio contenga información."""
    if not valor.strip():
        raise ValueError(f"{campo} no puede estar vacío.")


def _validar_no_negativo(
    valor: Decimal | None,
    campo: str,
) -> None:
    """Valida magnitudes monetarias o físicas que no admiten valores negativos."""
    if valor is not None and valor < 0:
        raise ValueError(f"{campo} no puede ser negativo.")


@dataclass(frozen=True, slots=True)
class RegistroPrecioMayorista:
    """
    Observación canónica de precio mayorista SIPSA.

    Un registro representa un único producto, mercado y fecha.

    ``precio_kg`` puede ser ``None`` cuando DANE reporta el valor como no
    disponible. Esto evita confundir ausencia de observación con precio cero.
    """

    fecha: date
    producto: str
    categoria: str
    ciudad: str
    mercado: str
    precio_kg: Decimal | None
    variacion: Decimal | None
    fuente: str
    archivo_fuente: str

    def __post_init__(self) -> None:
        """Comprueba invariantes fundamentales del registro."""
        _validar_texto(self.producto, "producto")
        _validar_texto(self.categoria, "categoria")
        _validar_texto(self.ciudad, "ciudad")
        _validar_texto(self.mercado, "mercado")
        _validar_texto(self.fuente, "fuente")
        _validar_texto(self.archivo_fuente, "archivo_fuente")
        _validar_no_negativo(self.precio_kg, "precio_kg")


@dataclass(frozen=True, slots=True)
class RegistroAbastecimiento:
    """
    Observación canónica de abastecimiento SIPSA.

    Un registro representa una cantidad recibida por un mercado mayorista
    desde una procedencia determinada para un producto y fecha concretos.

    Los códigos DIVIPOLA, ISO y CPC son cadenas deliberadamente, ya que son
    identificadores y pueden contener ceros iniciales.
    """

    fecha: date
    ciudad_mercado: str
    codigo_departamento_origen: str
    codigo_municipio_pais_origen: str
    departamento_origen: str
    municipio_pais_origen: str
    grupo: str
    codigo_cpc: str
    producto: str
    cantidad_kg: Decimal
    fuente: str
    archivo_fuente: str
    hoja_fuente: str

    def __post_init__(self) -> None:
        """Comprueba invariantes fundamentales del registro."""
        _validar_texto(self.ciudad_mercado, "ciudad_mercado")
        _validar_texto(
            self.codigo_departamento_origen,
            "codigo_departamento_origen",
        )
        _validar_texto(
            self.codigo_municipio_pais_origen,
            "codigo_municipio_pais_origen",
        )
        _validar_texto(self.departamento_origen, "departamento_origen")
        _validar_texto(self.municipio_pais_origen, "municipio_pais_origen")
        _validar_texto(self.grupo, "grupo")
        _validar_texto(self.codigo_cpc, "codigo_cpc")
        _validar_texto(self.producto, "producto")
        _validar_texto(self.fuente, "fuente")
        _validar_texto(self.archivo_fuente, "archivo_fuente")
        _validar_texto(self.hoja_fuente, "hoja_fuente")
        _validar_no_negativo(self.cantidad_kg, "cantidad_kg")
