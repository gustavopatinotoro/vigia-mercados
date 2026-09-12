"""
Parser de observaciones climáticas IDEAM.

Convierte registros JSON procedentes de Socrata en contratos canónicos
del dominio climático de VIGÍA.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal, InvalidOperation

from vigia.dominio.clima import (
    ObservacionClimatica,
    VariableClimatica,
)


class ErrorParserObservacionIdeam(RuntimeError):
    """Error al interpretar una observación climática IDEAM."""


CAMPOS_OBLIGATORIOS = (
    "codigoestacion",
    "codigosensor",
    "fechaobservacion",
    "valorobservado",
    "nombreestacion",
    "departamento",
    "municipio",
    "latitud",
    "longitud",
    "descripcionsensor",
    "unidadmedida",
)


def _texto(
    registro: dict[str, object],
    campo: str,
) -> str:
    """Obtiene un campo textual obligatorio."""
    valor = registro.get(campo)

    if not isinstance(valor, str):
        raise ErrorParserObservacionIdeam(f"Campo IDEAM inválido {campo!r}: {valor!r}")

    texto = valor.strip()

    if not texto:
        raise ErrorParserObservacionIdeam(f"Campo IDEAM vacío: {campo!r}")

    return texto


def _decimal(
    registro: dict[str, object],
    campo: str,
) -> Decimal:
    """Convierte un campo numérico textual a Decimal."""
    texto = _texto(
        registro,
        campo,
    )

    try:
        return Decimal(texto)
    except InvalidOperation as exc:
        raise ErrorParserObservacionIdeam(
            f"Valor decimal IDEAM inválido en {campo!r}: {texto!r}"
        ) from exc


def _fecha(
    registro: dict[str, object],
) -> datetime:
    """Convierte la fecha ISO publicada por Socrata."""
    texto = _texto(
        registro,
        "fechaobservacion",
    )

    try:
        return datetime.fromisoformat(texto)
    except ValueError as exc:
        raise ErrorParserObservacionIdeam(f"Fecha IDEAM inválida: {texto!r}") from exc


def parsear_observaciones_ideam(
    registros: list[dict[str, object]],
    *,
    variable: VariableClimatica,
) -> Iterator[ObservacionClimatica]:
    """Convierte registros Socrata en observaciones climáticas canónicas."""
    for indice, registro in enumerate(
        registros,
        start=1,
    ):
        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in registro]

        if faltantes:
            raise ErrorParserObservacionIdeam(
                f"Registro IDEAM {indice} incompleto. Campos faltantes: {faltantes!r}"
            )

        try:
            yield ObservacionClimatica(
                codigo_estacion=_texto(
                    registro,
                    "codigoestacion",
                ),
                codigo_sensor=_texto(
                    registro,
                    "codigosensor",
                ),
                fecha=_fecha(registro),
                variable=variable,
                valor=_decimal(
                    registro,
                    "valorobservado",
                ),
                unidad=_texto(
                    registro,
                    "unidadmedida",
                ),
                nombre_estacion=_texto(
                    registro,
                    "nombreestacion",
                ),
                departamento=_texto(
                    registro,
                    "departamento",
                ),
                municipio=_texto(
                    registro,
                    "municipio",
                ),
                latitud=_decimal(
                    registro,
                    "latitud",
                ),
                longitud=_decimal(
                    registro,
                    "longitud",
                ),
                descripcion_sensor=_texto(
                    registro,
                    "descripcionsensor",
                ),
            )

        except ValueError as exc:
            raise ErrorParserObservacionIdeam(f"Registro IDEAM {indice} inválido: {exc}") from exc
