"""
Agregación determinista de microdatos SIPSA_A.

Transforma registros fuente de abastecimiento en flujos diarios agregados
por producto, mercado y origen territorial.

La agregación utiliza SQLite como almacenamiento intermedio para mantener
acotado el consumo de memoria. Las cantidades se almacenan como texto y se
suman mediante Decimal; nunca se convierten a float.

Una repetición exacta de una fila fuente no se elimina. SIPSA no publica un
identificador transaccional que permita demostrar que dos filas idénticas
representan el mismo movimiento físico.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable, Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path

from vigia.dominio.sipsa import (
    ObservacionAbastecimientoDiarioSipsa,
    RegistroAbastecimiento,
)


class ErrorAgregacionAbastecimientoSipsa(RuntimeError):
    """Error producido al construir la serie diaria SIPSA_A."""


def _sumar_decimales_texto(
    acumulado: str,
    nuevo: str,
) -> str:
    """Suma dos cantidades Decimal representadas como texto."""
    return str(Decimal(acumulado) + Decimal(nuevo))


def _crear_base_temporal(
    ruta_bd: Path,
) -> sqlite3.Connection:
    """Crea una base SQLite limpia para la agregación."""
    ruta_bd.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if ruta_bd.exists():
        if not ruta_bd.is_file():
            raise ErrorAgregacionAbastecimientoSipsa(
                f"La ruta temporal no corresponde a un archivo: {ruta_bd}"
            )

        ruta_bd.unlink()

    conexion = sqlite3.connect(ruta_bd)

    conexion.execute("PRAGMA journal_mode = OFF")
    conexion.execute("PRAGMA synchronous = OFF")
    conexion.execute("PRAGMA temp_store = MEMORY")
    conexion.execute("PRAGMA cache_size = -100000")

    conexion.create_function(
        "sumar_decimal_exacto",
        2,
        _sumar_decimales_texto,
        deterministic=True,
    )

    conexion.execute(
        """
        CREATE TABLE abastecimiento (
            fecha TEXT NOT NULL,
            producto TEXT NOT NULL,
            mercado_destino TEXT NOT NULL,

            codigo_departamento_origen TEXT NOT NULL,
            codigo_municipio_pais_origen TEXT NOT NULL,

            departamento_origen TEXT NOT NULL,
            municipio_pais_origen TEXT NOT NULL,

            grupo TEXT NOT NULL,
            codigo_cpc TEXT NOT NULL,

            cantidad_kg TEXT NOT NULL,
            numero_registros_fuente INTEGER NOT NULL,

            fuente TEXT NOT NULL,
            archivo_fuente TEXT NOT NULL,

            PRIMARY KEY (
                fecha,
                producto,
                mercado_destino,
                codigo_departamento_origen,
                codigo_municipio_pais_origen
            )
        )
        """
    )

    return conexion


_SQL_AGREGAR = """
INSERT INTO abastecimiento (
    fecha,
    producto,
    mercado_destino,
    codigo_departamento_origen,
    codigo_municipio_pais_origen,
    departamento_origen,
    municipio_pais_origen,
    grupo,
    codigo_cpc,
    cantidad_kg,
    numero_registros_fuente,
    fuente,
    archivo_fuente
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)

ON CONFLICT (
    fecha,
    producto,
    mercado_destino,
    codigo_departamento_origen,
    codigo_municipio_pais_origen
)
DO UPDATE SET
    cantidad_kg = sumar_decimal_exacto(
        abastecimiento.cantidad_kg,
        excluded.cantidad_kg
    ),
    numero_registros_fuente =
        abastecimiento.numero_registros_fuente + 1

WHERE
    abastecimiento.departamento_origen
        = excluded.departamento_origen
    AND abastecimiento.municipio_pais_origen
        = excluded.municipio_pais_origen
    AND abastecimiento.grupo
        = excluded.grupo
    AND abastecimiento.codigo_cpc
        = excluded.codigo_cpc
    AND abastecimiento.fuente
        = excluded.fuente
    AND abastecimiento.archivo_fuente
        = excluded.archivo_fuente
"""


def _agregar_registro(
    conexion: sqlite3.Connection,
    registro: RegistroAbastecimiento,
) -> None:
    """Inserta o agrega exactamente un registro fuente."""
    cursor = conexion.execute(
        _SQL_AGREGAR,
        (
            registro.fecha.isoformat(),
            registro.producto,
            registro.ciudad_mercado,
            registro.codigo_departamento_origen,
            registro.codigo_municipio_pais_origen,
            registro.departamento_origen,
            registro.municipio_pais_origen,
            registro.grupo,
            registro.codigo_cpc,
            str(registro.cantidad_kg),
            registro.fuente,
            registro.archivo_fuente,
        ),
    )

    if cursor.rowcount != 0:
        return

    raise ErrorAgregacionAbastecimientoSipsa(
        "Se detectaron atributos contradictorios para la misma clave "
        "analítica de abastecimiento: "
        f"fecha={registro.fecha.isoformat()!r}, "
        f"producto={registro.producto!r}, "
        f"mercado={registro.ciudad_mercado!r}, "
        "origen="
        f"{registro.codigo_departamento_origen!r}/"
        f"{registro.codigo_municipio_pais_origen!r}."
    )


def agregar_abastecimiento_diario_sipsa(
    registros: Iterable[RegistroAbastecimiento],
    *,
    ruta_bd_temporal: Path,
    confirmar_cada: int = 10_000,
) -> Iterator[ObservacionAbastecimientoDiarioSipsa]:
    """
    Agrega registros SIPSA_A a granularidad diaria producto-mercado-origen.

    La clave analítica es:

    ``fecha + producto + mercado + departamento_origen + municipio_origen``.

    Las cantidades de todos los registros que comparten la clave se suman
    exactamente mediante Decimal.

    CPC, grupo, nombres territoriales, fuente y archivo deben ser invariantes
    dentro de una misma clave. Una contradicción detiene el procesamiento.

    Los resultados se emiten en orden determinista por clave.
    """
    if confirmar_cada <= 0:
        raise ValueError("confirmar_cada debe ser estrictamente positivo.")

    conexion = _crear_base_temporal(ruta_bd_temporal)

    total_fuente = 0

    try:
        for registro in registros:
            _agregar_registro(
                conexion,
                registro,
            )

            total_fuente += 1

            if total_fuente % confirmar_cada == 0:
                conexion.commit()

        conexion.commit()

        if total_fuente == 0:
            raise ErrorAgregacionAbastecimientoSipsa(
                "No se recibieron registros de abastecimiento."
            )

        cursor = conexion.execute(
            """
            SELECT
                fecha,
                producto,
                mercado_destino,
                codigo_departamento_origen,
                codigo_municipio_pais_origen,
                departamento_origen,
                municipio_pais_origen,
                grupo,
                codigo_cpc,
                cantidad_kg,
                numero_registros_fuente,
                fuente,
                archivo_fuente
            FROM abastecimiento
            ORDER BY
                fecha,
                producto,
                mercado_destino,
                codigo_departamento_origen,
                codigo_municipio_pais_origen
            """
        )

        for fila in cursor:
            (
                fecha_texto,
                producto,
                mercado_destino,
                codigo_departamento_origen,
                codigo_municipio_pais_origen,
                departamento_origen,
                municipio_pais_origen,
                grupo,
                codigo_cpc,
                cantidad_texto,
                numero_registros_fuente,
                fuente,
                archivo_fuente,
            ) = fila

            yield ObservacionAbastecimientoDiarioSipsa(
                fecha=date.fromisoformat(fecha_texto),
                producto=producto,
                mercado_destino=mercado_destino,
                codigo_departamento_origen=(codigo_departamento_origen),
                codigo_municipio_pais_origen=(codigo_municipio_pais_origen),
                departamento_origen=departamento_origen,
                municipio_pais_origen=municipio_pais_origen,
                grupo=grupo,
                codigo_cpc=codigo_cpc,
                cantidad_kg=Decimal(cantidad_texto),
                numero_registros_fuente=(numero_registros_fuente),
                fuente=fuente,
                archivo_fuente=archivo_fuente,
            )

    except sqlite3.Error as exc:
        raise ErrorAgregacionAbastecimientoSipsa(
            f"Falló la agregación SQLite de SIPSA_A: {exc}"
        ) from exc

    finally:
        conexion.close()


def eliminar_base_temporal_abastecimiento(
    ruta_bd_temporal: Path,
) -> None:
    """Elimina de forma segura una base temporal de agregación."""
    try:
        ruta_bd_temporal.unlink(missing_ok=True)
    except OSError as exc:
        raise ErrorAgregacionAbastecimientoSipsa(
            f"No fue posible eliminar la base temporal de abastecimiento: {ruta_bd_temporal}"
        ) from exc

    for sufijo in (
        "-journal",
        "-shm",
        "-wal",
    ):
        ruta_auxiliar = Path(f"{ruta_bd_temporal}{sufijo}")

        try:
            os.remove(ruta_auxiliar)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise ErrorAgregacionAbastecimientoSipsa(
                f"No fue posible eliminar un archivo temporal de SQLite: {ruta_auxiliar}"
            ) from exc
