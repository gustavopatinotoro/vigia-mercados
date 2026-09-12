"""
Pruebas de contratos de alias territoriales.
"""

import pytest

from vigia.dominio.territorio import AliasTerritorial


def test_crea_alias_territorial() -> None:
    """Acepta una asociación territorial explícita."""
    alias = AliasTerritorial(
        fuente="IDEAM",
        departamento_fuente="Valle Del Cauca",
        nombre_fuente="Cali",
        codigo_divipola="76001",
    )

    assert alias.codigo_divipola == "76001"


def test_rechaza_divipola_invalido() -> None:
    """Impide alias con códigos territoriales inválidos."""
    with pytest.raises(
        ValueError,
        match="exactamente 5 caracteres",
    ):
        AliasTerritorial(
            fuente="IDEAM",
            departamento_fuente="Valle Del Cauca",
            nombre_fuente="Cali",
            codigo_divipola="7601",
        )


def test_rechaza_fuente_vacia() -> None:
    """Todo alias debe conservar su procedencia."""
    with pytest.raises(
        ValueError,
        match="fuente no puede estar vacía",
    ):
        AliasTerritorial(
            fuente=" ",
            departamento_fuente="Valle Del Cauca",
            nombre_fuente="Cali",
            codigo_divipola="76001",
        )
