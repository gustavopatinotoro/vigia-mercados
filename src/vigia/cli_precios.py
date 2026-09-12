"""
CLI para generar la serie histórica mensual de precios SIPSA_P.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from vigia.aplicacion import (
    ErrorGeneracionPreciosMensuales,
    generar_serie_historica_precios_sipsa,
)


def _crear_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos de la CLI."""
    parser = argparse.ArgumentParser(
        description=("Genera la serie mensual histórica SIPSA_P 2013-2024 de forma reproducible."),
    )

    parser.add_argument(
        "--fuentes",
        type=Path,
        default=Path("datos/auditoria"),
        help=("Directorio que contiene los ZIP oficiales SIPSA_P. Por defecto: datos/auditoria"),
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("artefactos/sipsa"),
        help=("Directorio de salida de los artefactos. Por defecto: artefactos/sipsa"),
    )

    parser.add_argument(
        "--nombre",
        default="precios_mensuales_2013_2024",
        help="Nombre base de los artefactos.",
    )

    return parser


def main() -> int:
    """Ejecuta la generación histórica desde línea de comandos."""
    parser = _crear_parser()
    argumentos = parser.parse_args()

    try:
        resultado = generar_serie_historica_precios_sipsa(
            directorio_fuentes=argumentos.fuentes,
            directorio_salida=argumentos.salida,
            nombre=argumentos.nombre,
        )

    except (
        ErrorGeneracionPreciosMensuales,
        ValueError,
    ) as exc:
        parser.error(str(exc))

    print("=" * 80)
    print("VIGÍA - SERIE HISTÓRICA MENSUAL SIPSA_P")
    print("=" * 80)

    for estadistica in resultado.estadisticas_archivos:
        print()
        print(estadistica.periodo)
        print(f"  ZIP: {estadistica.archivo_zip}")
        print(f"  CSV: {estadistica.archivo_csv}")
        print(f"  Perfil: {estadistica.perfil}")
        print(f"  Observaciones: {estadistica.observaciones}")
        print(f"  Conflictos: {estadistica.conflictos}")

    print()
    print("=" * 80)
    print("RESULTADO GLOBAL")
    print("=" * 80)

    print(f"Observaciones: {resultado.observaciones}")
    print(f"Claves candidatas: {resultado.claves_candidatas}")
    print(f"Conflictos: {resultado.conflictos}")
    print(f"Observaciones conflictivas: {resultado.observaciones_conflictivas}")
    print(f"Observaciones excedentes: {resultado.observaciones_excedentes}")

    print()
    print(f"Datos: {resultado.persistencia.ruta_datos}")
    print(f"Conflictos: {resultado.persistencia.ruta_conflictos}")
    print(f"Manifiesto: {resultado.persistencia.ruta_manifiesto}")

    print()
    print(f"SHA256 datos: {resultado.persistencia.sha256_datos}")
    print(f"SHA256 conflictos: {resultado.persistencia.sha256_conflictos}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
