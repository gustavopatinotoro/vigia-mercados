"""
Contratos analíticos para series históricas de precios SIPSA.

Este módulo representa observaciones mensuales ya normalizadas para análisis
temporal. No conoce detalles de archivos CSV, ZIP, Excel ni versiones del
esquema externo publicado por DANE.

La identidad natural de una observación mensual es:

    fecha_mes + producto + mercado

El código CPC es un atributo taxonómico y puede no estar disponible en
periodos históricos. El grupo también es un atributo observado y no forma
parte de la identidad del producto.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


def _validar_texto(valor: str, campo: str) -> None:
    """Valida que un texto obligatorio contenga información."""
    if not valor.strip():
        raise ValueError(f"{campo} no puede estar vacío.")


def _validar_codigo_opcional(
    valor: str | None,
    campo: str,
) -> None:
    """Valida un código opcional cuando está presente."""
    if valor is not None and not valor.strip():
        raise ValueError(f"{campo} debe ser None o contener información.")


@dataclass(frozen=True, slots=True)
class ObservacionPrecioMensualSipsa:
    """
    Observación mensual canónica de precio mayorista SIPSA.

    La fecha se representa mediante el primer día del mes observado.
    Esto permite utilizar ``date`` sin introducir una estructura temporal
    específica adicional.

    ``codigo_cpc`` puede ser ``None`` para periodos históricos donde DANE no
    publicó ese atributo.

    ``precio_promedio_kg`` representa pesos colombianos por kilogramo y debe
    ser estrictamente positivo.
    """

    fecha_mes: date
    producto: str
    mercado: str
    grupo: str
    codigo_cpc: str | None
    precio_promedio_kg: Decimal
    fuente: str
    archivo_fuente: str

    def __post_init__(self) -> None:
        """Comprueba las invariantes del contrato analítico."""
        if self.fecha_mes.day != 1:
            raise ValueError("fecha_mes debe corresponder al primer día del mes.")

        _validar_texto(self.producto, "producto")
        _validar_texto(self.mercado, "mercado")
        _validar_texto(self.grupo, "grupo")
        _validar_codigo_opcional(
            self.codigo_cpc,
            "codigo_cpc",
        )
        _validar_texto(self.fuente, "fuente")
        _validar_texto(
            self.archivo_fuente,
            "archivo_fuente",
        )

        if self.precio_promedio_kg <= 0:
            raise ValueError("precio_promedio_kg debe ser mayor que cero.")

    @property
    def clave_natural(self) -> tuple[date, str, str]:
        """
        Devuelve la identidad natural observada de la serie.

        El grupo y CPC se excluyen deliberadamente porque son atributos
        taxonómicos y pueden cambiar o no estar disponibles históricamente.
        """
        return (
            self.fecha_mes,
            self.producto,
            self.mercado,
        )
