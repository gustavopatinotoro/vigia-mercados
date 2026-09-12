"""
Pruebas de normalización territorial.
"""

import pytest

from vigia.infraestructura.territorio import (
    normalizar_nombre_territorial,
)


@pytest.mark.parametrize(
    ("origen", "esperado"),
    [
        ("MANIZALES", "manizales"),
        ("Manizales", "manizales"),
        ("CHINCHINÁ", "chinchina"),
        ("Chinchina", "chinchina"),
        ("BELALCÁZAR", "belalcazar"),
        ("San José", "san jose"),
        ("San Jose", "san jose"),
        ("  LA   DORADA  ", "la dorada"),
        ("VILLAMARÍA", "villamaria"),
        ("Villamaria", "villamaria"),
    ],
)
def test_normaliza_nombre_territorial(
    origen: str,
    esperado: str,
) -> None:
    """Normaliza variantes ortográficas equivalentes."""
    assert normalizar_nombre_territorial(origen) == esperado


def test_rechaza_nombre_vacio() -> None:
    """Impide normalizar territorios sin nombre."""
    with pytest.raises(
        ValueError,
        match="no puede estar vacío",
    ):
        normalizar_nombre_territorial("   ")
