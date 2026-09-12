"""
Pruebas del parser de observaciones climáticas IDEAM.
"""

from decimal import Decimal

import pytest

from vigia.dominio.clima import VariableClimatica
from vigia.infraestructura.ideam.parser_observaciones import (
    ErrorParserObservacionIdeam,
    parsear_observaciones_ideam,
)


def _registro_precipitacion() -> dict[str, object]:
    """Construye una observación representativa de IDEAM."""
    return {
        "codigoestacion": "0048015050",
        "codigosensor": "0257",
        "fechaobservacion": "2024-05-07T21:04:00.000",
        "valorobservado": "0",
        "nombreestacion": "AEROPUERTO VASQUEZ COBO",
        "departamento": "AMAZONAS",
        "municipio": "LETICIA",
        "zonahidrografica": "AMAZONAS - DIRECTOS",
        "latitud": "-4.19386111",
        "longitud": "-69.94091667",
        "descripcionsensor": "GPRS - PRECIPITACIÓN",
        "unidadmedida": "mm",
    }


def test_parsea_precipitacion() -> None:
    """Convierte correctamente una observación de precipitación."""
    observaciones = list(
        parsear_observaciones_ideam(
            [_registro_precipitacion()],
            variable=VariableClimatica.PRECIPITACION,
        )
    )

    assert len(observaciones) == 1

    observacion = observaciones[0]

    assert observacion.codigo_estacion == "0048015050"
    assert observacion.codigo_sensor == "0257"
    assert observacion.valor == Decimal("0")
    assert observacion.unidad == "mm"
    assert observacion.fecha.isoformat() == "2024-05-07T21:04:00"


def test_preserva_registros_duplicados() -> None:
    """El parser no elimina observaciones sin una regla explícita."""
    registro = _registro_precipitacion()

    observaciones = list(
        parsear_observaciones_ideam(
            [
                registro.copy(),
                registro.copy(),
            ],
            variable=VariableClimatica.PRECIPITACION,
        )
    )

    assert len(observaciones) == 2


def test_rechaza_campo_faltante() -> None:
    """Detecta cambios o registros incompletos en la fuente."""
    registro = _registro_precipitacion()
    del registro["valorobservado"]

    with pytest.raises(
        ErrorParserObservacionIdeam,
        match="Campos faltantes",
    ):
        list(
            parsear_observaciones_ideam(
                [registro],
                variable=VariableClimatica.PRECIPITACION,
            )
        )


def test_rechaza_valor_no_numerico() -> None:
    """Rechaza valores observados que no puedan convertirse."""
    registro = _registro_precipitacion()
    registro["valorobservado"] = "sin-dato"

    with pytest.raises(
        ErrorParserObservacionIdeam,
        match="Valor decimal IDEAM inválido",
    ):
        list(
            parsear_observaciones_ideam(
                [registro],
                variable=VariableClimatica.PRECIPITACION,
            )
        )


def test_rechaza_fecha_invalida() -> None:
    """Rechaza fechas incompatibles con el contrato IDEAM."""
    registro = _registro_precipitacion()
    registro["fechaobservacion"] = "fecha-invalida"

    with pytest.raises(
        ErrorParserObservacionIdeam,
        match="Fecha IDEAM inválida",
    ):
        list(
            parsear_observaciones_ideam(
                [registro],
                variable=VariableClimatica.PRECIPITACION,
            )
        )
