"""
Parser del catálogo nacional de estaciones IDEAM.
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal, InvalidOperation

from vigia.dominio.clima import EstacionIdeam


class ErrorParserEstacionIdeam(RuntimeError):
    """Error al interpretar una estación publicada por IDEAM."""


CAMPOS_OBLIGATORIOS = (
    "codigo",
    "nombre",
    "categoria",
    "tecnologia",
    "estado",
    "departamento",
    "municipio",
    "latitud",
    "longitud",
    "entidad",
)


def _texto(
    registro: dict[str, object],
    campo: str,
) -> str:
    """Obtiene un campo textual obligatorio."""
    valor = registro.get(campo)

    if not isinstance(valor, str):
        raise ErrorParserEstacionIdeam(f"Campo IDEAM inválido {campo!r}: {valor!r}")

    texto = valor.strip()

    if not texto:
        raise ErrorParserEstacionIdeam(f"Campo IDEAM vacío: {campo!r}")

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
        raise ErrorParserEstacionIdeam(
            f"Valor decimal IDEAM inválido en {campo!r}: {texto!r}"
        ) from exc


def _altitud(
    registro: dict[str, object],
) -> Decimal | None:
    """Obtiene la altitud cuando está disponible."""
    valor = registro.get("altitud")

    if valor is None:
        return None

    if not isinstance(valor, str):
        raise ErrorParserEstacionIdeam(f"Campo IDEAM inválido 'altitud': {valor!r}")

    texto = valor.strip()

    if not texto:
        return None

    try:
        return Decimal(texto)
    except InvalidOperation as exc:
        raise ErrorParserEstacionIdeam(f"Altitud IDEAM inválida: {texto!r}") from exc


def parsear_estaciones_ideam(
    registros: list[dict[str, object]],
) -> Iterator[EstacionIdeam]:
    """Convierte registros Socrata en estaciones canónicas."""
    for indice, registro in enumerate(
        registros,
        start=1,
    ):
        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in registro]

        if faltantes:
            raise ErrorParserEstacionIdeam(
                f"Registro de estación IDEAM {indice} incompleto. Campos faltantes: {faltantes!r}"
            )

        try:
            yield EstacionIdeam(
                codigo=_texto(
                    registro,
                    "codigo",
                ),
                nombre=_texto(
                    registro,
                    "nombre",
                ),
                categoria=_texto(
                    registro,
                    "categoria",
                ),
                tecnologia=_texto(
                    registro,
                    "tecnologia",
                ),
                estado=_texto(
                    registro,
                    "estado",
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
                altitud_m=_altitud(registro),
                entidad=_texto(
                    registro,
                    "entidad",
                ),
            )

        except ValueError as exc:
            raise ErrorParserEstacionIdeam(
                f"Registro de estación IDEAM {indice} inválido: {exc}"
            ) from exc
