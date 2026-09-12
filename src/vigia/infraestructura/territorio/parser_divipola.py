"""
Parser del catálogo territorial nacional DIVIPOLA.

Convierte registros JSON publicados en Datos Abiertos Colombia en
entidades territoriales canónicas de VIGÍA.
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal, InvalidOperation

from vigia.dominio.territorio import (
    EntidadTerritorialCanonica,
    TipoEntidadTerritorial,
)


class ErrorParserDivipola(RuntimeError):
    """Error al interpretar un registro territorial DIVIPOLA."""


CAMPOS_OBLIGATORIOS = (
    "cod_dpto",
    "dpto",
    "cod_mpio",
    "nom_mpio",
    "tipo_municipio",
    "latitud",
    "longitud",
)


def _texto(
    registro: dict[str, object],
    campo: str,
) -> str:
    """Obtiene un campo textual obligatorio."""
    valor = registro.get(campo)

    if not isinstance(valor, str):
        raise ErrorParserDivipola(f"Campo DIVIPOLA inválido {campo!r}: {valor!r}")

    texto = valor.strip()

    if not texto:
        raise ErrorParserDivipola(f"Campo DIVIPOLA vacío: {campo!r}")

    return texto


def _decimal(
    registro: dict[str, object],
    campo: str,
) -> Decimal:
    """
    Convierte un campo decimal DIVIPOLA.

    La fuente pública presenta coordenadas tanto con punto como con coma
    decimal. Ambas representaciones se normalizan de forma determinista.
    """
    texto_original = _texto(
        registro,
        campo,
    )

    texto_normalizado = texto_original.replace(",", ".")

    try:
        return Decimal(texto_normalizado)
    except InvalidOperation as exc:
        raise ErrorParserDivipola(
            f"Valor decimal DIVIPOLA inválido en {campo!r}: {texto_original!r}"
        ) from exc


def _tipo(
    registro: dict[str, object],
) -> TipoEntidadTerritorial:
    """Convierte el tipo textual publicado por DIVIPOLA."""
    texto = _texto(
        registro,
        "tipo_municipio",
    )

    try:
        return TipoEntidadTerritorial(texto)
    except ValueError as exc:
        raise ErrorParserDivipola(f"Tipo territorial DIVIPOLA desconocido: {texto!r}") from exc


def parsear_divipola(
    registros: list[dict[str, object]],
) -> Iterator[EntidadTerritorialCanonica]:
    """Convierte registros Socrata en entidades territoriales canónicas."""
    for indice, registro in enumerate(
        registros,
        start=1,
    ):
        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in registro]

        if faltantes:
            raise ErrorParserDivipola(
                f"Registro DIVIPOLA {indice} incompleto. Campos faltantes: {faltantes!r}"
            )

        try:
            yield EntidadTerritorialCanonica(
                codigo_divipola=_texto(
                    registro,
                    "cod_mpio",
                ),
                codigo_departamento=_texto(
                    registro,
                    "cod_dpto",
                ),
                departamento=_texto(
                    registro,
                    "dpto",
                ),
                nombre=_texto(
                    registro,
                    "nom_mpio",
                ),
                tipo=_tipo(registro),
                latitud=_decimal(
                    registro,
                    "latitud",
                ),
                longitud=_decimal(
                    registro,
                    "longitud",
                ),
            )

        except ValueError as exc:
            raise ErrorParserDivipola(f"Registro DIVIPOLA {indice} inválido: {exc}") from exc
