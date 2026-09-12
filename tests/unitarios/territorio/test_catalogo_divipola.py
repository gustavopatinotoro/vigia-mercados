"""
Pruebas de carga del catálogo DIVIPOLA.
"""

from unittest.mock import Mock

from vigia.infraestructura.territorio import (
    DATASET_DIVIPOLA,
    cargar_catalogo_divipola,
)


def test_carga_catalogo_desde_socrata() -> None:
    cliente = Mock()

    cliente.consultar.return_value = [
        {
            "cod_dpto": "17",
            "dpto": "CALDAS",
            "cod_mpio": "17001",
            "nom_mpio": "MANIZALES",
            "tipo_municipio": "Municipio",
            "latitud": "5.06889",
            "longitud": "-75.51738",
        }
    ]

    catalogo = cargar_catalogo_divipola(
        cliente=cliente,
    )

    assert len(catalogo) == 1
    assert catalogo[0].codigo_divipola == "17001"

    cliente.consultar.assert_called_once()

    llamada = cliente.consultar.call_args

    assert llamada.args[0] == DATASET_DIVIPOLA
