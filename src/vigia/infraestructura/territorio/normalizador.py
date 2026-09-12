"""
Normalización determinista de nombres territoriales.

Permite comparar nombres provenientes de fuentes públicas distintas sin
convertir el nombre textual en identidad primaria.
"""

from __future__ import annotations

import unicodedata


def normalizar_nombre_territorial(valor: str) -> str:
    """
    Normaliza un nombre territorial para comparación determinista.

    La operación:
    - elimina espacios periféricos;
    - convierte a minúsculas Unicode;
    - elimina diacríticos;
    - compacta espacios internos.
    """
    if not valor.strip():
        raise ValueError("El nombre territorial no puede estar vacío.")

    normalizado = unicodedata.normalize(
        "NFKD",
        valor.strip().casefold(),
    )

    sin_diacriticos = "".join(
        caracter for caracter in normalizado if not unicodedata.combining(caracter)
    )

    return " ".join(sin_diacriticos.split())
