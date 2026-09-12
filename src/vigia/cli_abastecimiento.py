"""
CLI para generar la serie diaria agregada de abastecimiento SIPSA_A.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from vigia.aplicacion import (
    ErrorGeneracionAbastecimiento,
    generar_serie_abastecimiento_sipsa,
)


def _crear_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos de la CLI."""
    parser = argparse.ArgumentParser(
        description=("Genera la serie diaria agregada SIPSA_A de forma reproducible."),
    )

    parser.add_argument(
        "--fuente",
        type=Path,
        default=Path("datos/sipsa/abastecimiento/anex-Microdato-abastecimiento-2026.xlsx"),
        help="XLSX oficial de microdatos SIPSA_A.",
    )

    parser.add_argument(
        "--salida",
        type=Path,
        default=Path("artefactos/sipsa"),
        help=("Directorio de salida. Por defecto: artefactos/sipsa"),
    )

    parser.add_argument(
        "--temporal",
        type=Path,
        default=Path("artefactos/auditoria/agregacion_abastecimiento_2026.sqlite"),
        help="Base SQLite temporal utilizada durante la agregación.",
    )

    parser.add_argument(
        "--nombre",
        default="abastecimiento_diario_2026",
        help="Nombre base de los artefactos.",
    )

    return parser


def main() -> int:
    """Ejecuta la generación de la serie SIPSA_A."""
    parser = _crear_parser()
    argumentos = parser.parse_args()

    try:
        resultado = generar_serie_abastecimiento_sipsa(
            ruta_fuente=argumentos.fuente,
            directorio_salida=argumentos.salida,
            ruta_bd_temporal=argumentos.temporal,
            nombre=argumentos.nombre,
        )

    except ErrorGeneracionAbastecimiento as exc:
        parser.error(str(exc))

    persistencia = resultado.persistencia

    print("=" * 80)
    print("VIGÍA - SERIE DIARIA DE ABASTECIMIENTO SIPSA_A")
    print("=" * 80)

    print(f"Fuente: {resultado.archivo_fuente}")

    print()
    print(f"Observaciones: {persistencia.observaciones}")
    print(f"Registros fuente: {persistencia.registros_fuente}")

    print()
    print(f"Fecha mínima: {persistencia.fecha_minima}")
    print(f"Fecha máxima: {persistencia.fecha_maxima}")

    print()
    print(f"Productos: {persistencia.productos}")
    print(f"Mercados: {persistencia.mercados}")
    print(f"CPC: {persistencia.cpc}")
    print(f"Orígenes: {persistencia.origenes}")

    print()
    print(f"Cantidad total kg: {persistencia.cantidad_total_kg}")

    print()
    print(f"Datos: {persistencia.ruta_datos}")
    print(f"Manifiesto: {persistencia.ruta_manifiesto}")

    print()
    print(f"SHA256 datos: {persistencia.sha256_datos}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
