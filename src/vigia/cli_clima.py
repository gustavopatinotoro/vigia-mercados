"""
Interfaz de línea de comandos para generación de series climáticas.

Uso:

python -m vigia.cli_clima \
    --inicio 2026-09-01 \
    --fin 2026-09-02
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from vigia.aplicacion.series_climaticas import (
    ErrorGeneracionSeriesClimaticas,
    generar_series_climaticas_territoriales,
)


def main() -> int:
    """Punto de entrada de la CLI climática."""
    argumentos = _crear_parser().parse_args()

    try:
        inicio = _parsear_fecha(argumentos.inicio)

        fin = _parsear_fecha(argumentos.fin)

        resultado = generar_series_climaticas_territoriales(
            inicio=inicio,
            fin=fin,
            directorio_salida=Path(argumentos.salida),
            nombre_base=argumentos.nombre,
            tamano_pagina=argumentos.tamano_pagina,
            timeout_segundos=argumentos.timeout,
            informar=print,
        )

    except (
        ValueError,
        ErrorGeneracionSeriesClimaticas,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    print()
    print("=" * 80)
    print("SERIE CLIMÁTICA GENERADA")
    print("=" * 80)

    print(
        "Periodo:",
        resultado.inicio,
        "→",
        resultado.fin,
    )

    print(
        "Estaciones catálogo:",
        resultado.estaciones_catalogo,
    )

    print(
        "Estaciones territorializadas:",
        resultado.estaciones_territorializadas,
    )

    print(
        "Estaciones no territorializadas:",
        resultado.estaciones_no_territorializadas,
    )

    for estadistica in resultado.estadisticas:
        print()
        print(estadistica.variable.value.upper())

        print(
            "  registros descargados:",
            estadistica.registros_descargados,
        )

        print(
            "  observaciones únicas:",
            estadistica.observaciones_unicas,
        )

        print(
            "  observaciones consolidadas:",
            estadistica.observaciones_consolidadas,
        )

        print(
            "  estación-hora:",
            estadistica.observaciones_estacion_hora,
        )

        print(
            "  territorio-hora:",
            estadistica.observaciones_territorio_hora,
        )

        print(
            "  estaciones:",
            estadistica.estaciones_con_datos,
        )

        print(
            "  territorios:",
            estadistica.territorios_con_datos,
        )

    print()
    print(
        "Registros persistidos:",
        resultado.persistencia.registros,
    )

    print(
        "Datos:",
        resultado.persistencia.ruta_datos,
    )

    print(
        "Manifiesto:",
        resultado.persistencia.ruta_manifiesto,
    )

    print(
        "SHA-256:",
        resultado.persistencia.sha256,
    )

    return 0


def _crear_parser() -> argparse.ArgumentParser:
    """Construye el contrato público de argumentos."""
    parser = argparse.ArgumentParser(
        prog="vigia-clima",
        description=(
            "Genera series climáticas territoriales horarias a partir de datos oficiales IDEAM."
        ),
    )

    parser.add_argument(
        "--inicio",
        required=True,
        help=("Inicio incluido del intervalo. Formato: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS."),
    )

    parser.add_argument(
        "--fin",
        required=True,
        help=("Fin excluido del intervalo. Formato: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS."),
    )

    parser.add_argument(
        "--salida",
        default="artefactos/clima",
        help=("Directorio de salida. Predeterminado: artefactos/clima."),
    )

    parser.add_argument(
        "--nombre",
        default=None,
        help=("Nombre base opcional del artefacto."),
    )

    parser.add_argument(
        "--tamano-pagina",
        type=int,
        default=5000,
        help=("Número máximo de registros por página Socrata."),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help=("Timeout HTTP en segundos."),
    )

    return parser


def _parsear_fecha(
    valor: str,
) -> datetime:
    """Interpreta fecha o timestamp ISO 8601 sin zona horaria."""
    try:
        return datetime.fromisoformat(valor)
    except ValueError as exc:
        raise ValueError(f"Fecha inválida: {valor!r}.") from exc


if __name__ == "__main__":
    raise SystemExit(main())
