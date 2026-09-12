"""
Contratos de dominio para series analíticas de abastecimiento SIPSA_A.

Una observación representa el flujo total diario de un producto desde un
origen territorial hacia un mercado mayorista.

La cantidad corresponde a la suma de todas las observaciones fuente que
comparten la misma clave analítica. Las repeticiones exactas de la fuente
no se eliminan porque SIPSA no publica un identificador transaccional que
permita demostrar que sean duplicados.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

type ClaveAbastecimientoDiarioSipsa = tuple[
    date,
    str,
    str,
    str,
    str,
]


@dataclass(frozen=True, slots=True)
class ObservacionAbastecimientoDiarioSipsa:
    """
    Flujo diario agregado de abastecimiento SIPSA.

    La identidad analítica está determinada por:

    - fecha;
    - producto;
    - mercado destino;
    - código de departamento de origen;
    - código de municipio o país de origen.

    Grupo, CPC y nombres territoriales son atributos descriptivos y no
    forman parte de la identidad.
    """

    fecha: date
    producto: str
    mercado_destino: str

    codigo_departamento_origen: str
    codigo_municipio_pais_origen: str

    departamento_origen: str
    municipio_pais_origen: str

    grupo: str
    codigo_cpc: str

    cantidad_kg: Decimal

    numero_registros_fuente: int

    fuente: str
    archivo_fuente: str

    def __post_init__(self) -> None:
        """Valida invariantes básicas de la observación agregada."""
        campos_textuales = {
            "producto": self.producto,
            "mercado_destino": self.mercado_destino,
            "codigo_departamento_origen": self.codigo_departamento_origen,
            "codigo_municipio_pais_origen": self.codigo_municipio_pais_origen,
            "departamento_origen": self.departamento_origen,
            "municipio_pais_origen": self.municipio_pais_origen,
            "grupo": self.grupo,
            "codigo_cpc": self.codigo_cpc,
            "fuente": self.fuente,
            "archivo_fuente": self.archivo_fuente,
        }

        for nombre, valor in campos_textuales.items():
            if not valor.strip():
                raise ValueError(f"{nombre} no puede estar vacío.")

        if self.cantidad_kg <= 0:
            raise ValueError("cantidad_kg debe ser estrictamente positiva.")

        if self.numero_registros_fuente <= 0:
            raise ValueError("numero_registros_fuente debe ser estrictamente positivo.")

    @property
    def clave_natural(
        self,
    ) -> ClaveAbastecimientoDiarioSipsa:
        """Devuelve la clave analítica de la observación."""
        return (
            self.fecha,
            self.producto,
            self.mercado_destino,
            self.codigo_departamento_origen,
            self.codigo_municipio_pais_origen,
        )
