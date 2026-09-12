"""
Persistencia reproducible de la serie diaria de abastecimiento SIPSA_A.

Garantías:

- no carga toda la serie en memoria;
- valida unicidad de la clave analítica;
- ordena determinísticamente mediante SQLite;
- conserva Decimal como texto exacto;
- genera CSV.GZ reproducible byte a byte;
- genera manifiesto JSON reproducible;
- calcula SHA-256 de los artefactos.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path

from vigia.dominio.sipsa import (
    ObservacionAbastecimientoDiarioSipsa,
)


class ErrorPersistenciaAbastecimientoSipsa(RuntimeError):
    """Error durante la persistencia de la serie SIPSA_A."""


@dataclass(frozen=True, slots=True)
class ResultadoPersistenciaAbastecimiento:
    """Resultado de persistir la serie diaria de abastecimiento."""

    ruta_datos: Path
    ruta_manifiesto: Path

    observaciones: int
    registros_fuente: int

    fecha_minima: str
    fecha_maxima: str

    productos: int
    mercados: int
    cpc: int
    origenes: int

    cantidad_total_kg: Decimal

    sha256_datos: str


_CAMPOS = (
    "fecha",
    "producto",
    "mercado_destino",
    "codigo_departamento_origen",
    "codigo_municipio_pais_origen",
    "departamento_origen",
    "municipio_pais_origen",
    "grupo",
    "codigo_cpc",
    "cantidad_kg",
    "numero_registros_fuente",
    "fuente",
    "archivo_fuente",
)


def _validar_nombre_base(
    nombre: str,
) -> None:
    """Valida que el nombre no permita escapar del directorio destino."""
    if not nombre:
        raise ValueError("El nombre base no puede estar vacío.")

    if nombre in {".", ".."}:
        raise ValueError("El nombre base no es válido.")

    if Path(nombre).name != nombre:
        raise ValueError("El nombre base no puede contener rutas.")


def _sha256(
    ruta: Path,
) -> str:
    """Calcula SHA-256 mediante lectura incremental."""
    digest = hashlib.sha256()

    with ruta.open("rb") as archivo:
        while bloque := archivo.read(1024 * 1024):
            digest.update(bloque)

    return digest.hexdigest()


def _crear_base_temporal(
    ruta: Path,
) -> sqlite3.Connection:
    """Crea almacenamiento temporal para ordenamiento y validación."""
    if ruta.exists():
        ruta.unlink()

    conexion = sqlite3.connect(ruta)

    conexion.execute("PRAGMA journal_mode = OFF")
    conexion.execute("PRAGMA synchronous = OFF")
    conexion.execute("PRAGMA temp_store = MEMORY")
    conexion.execute("PRAGMA cache_size = -100000")

    conexion.execute(
        """
        CREATE TABLE observaciones (
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


def _insertar_observaciones(
    conexion: sqlite3.Connection,
    observaciones: Iterable[ObservacionAbastecimientoDiarioSipsa],
) -> int:
    """Carga las observaciones y valida unicidad canónica."""
    total = 0

    sql = """
    INSERT INTO observaciones (
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
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for observacion in observaciones:
        try:
            conexion.execute(
                sql,
                (
                    observacion.fecha.isoformat(),
                    observacion.producto,
                    observacion.mercado_destino,
                    observacion.codigo_departamento_origen,
                    observacion.codigo_municipio_pais_origen,
                    observacion.departamento_origen,
                    observacion.municipio_pais_origen,
                    observacion.grupo,
                    observacion.codigo_cpc,
                    str(observacion.cantidad_kg),
                    observacion.numero_registros_fuente,
                    observacion.fuente,
                    observacion.archivo_fuente,
                ),
            )

        except sqlite3.IntegrityError as exc:
            raise ErrorPersistenciaAbastecimientoSipsa(
                "Se recibió una clave analítica duplicada durante "
                "la persistencia: "
                f"{observacion.clave_natural!r}"
            ) from exc

        total += 1

        if total % 10_000 == 0:
            conexion.commit()

    conexion.commit()

    if total == 0:
        raise ErrorPersistenciaAbastecimientoSipsa("No se recibieron observaciones para persistir.")

    return total


def _escribir_csv_gzip(
    conexion: sqlite3.Connection,
    ruta: Path,
) -> None:
    """Genera el CSV.GZ en orden total reproducible."""
    temporal = Path(f"{ruta}.parcial")

    try:
        with (
            temporal.open("wb") as archivo_binario,
            gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=archivo_binario,
                mtime=0,
            ) as archivo_gzip,
            TextIOWrapper(
                archivo_gzip,
                encoding="utf-8",
                newline="",
            ) as archivo_texto,
        ):
            escritor = csv.writer(
                archivo_texto,
                lineterminator="\n",
            )

            escritor.writerow(_CAMPOS)

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
                    FROM observaciones
                    ORDER BY
                        fecha,
                        producto,
                        mercado_destino,
                        codigo_departamento_origen,
                        codigo_municipio_pais_origen
                    """
            )

            escritor.writerows(cursor)

        os.replace(
            temporal,
            ruta,
        )

    except OSError as exc:
        temporal.unlink(missing_ok=True)

        raise ErrorPersistenciaAbastecimientoSipsa(
            f"No fue posible escribir {ruta}: {exc}"
        ) from exc


def _obtener_estadisticas(
    conexion: sqlite3.Connection,
) -> tuple[
    str,
    str,
    int,
    int,
    int,
    int,
    int,
    int,
    Decimal,
    list[str],
]:
    """Calcula estadísticas exactas de la serie persistida."""
    fila = conexion.execute(
        """
        SELECT
            MIN(fecha),
            MAX(fecha),
            COUNT(*),
            SUM(numero_registros_fuente)
        FROM observaciones
        """
    ).fetchone()

    if fila is None:
        raise ErrorPersistenciaAbastecimientoSipsa("No fue posible obtener estadísticas.")

    fecha_minima = str(fila[0])
    fecha_maxima = str(fila[1])
    observaciones = int(fila[2])
    registros_fuente = int(fila[3])

    productos = int(
        conexion.execute(
            """
            SELECT COUNT(DISTINCT producto)
            FROM observaciones
            """
        ).fetchone()[0]
    )

    mercados = int(
        conexion.execute(
            """
            SELECT COUNT(DISTINCT mercado_destino)
            FROM observaciones
            """
        ).fetchone()[0]
    )

    cpc = int(
        conexion.execute(
            """
            SELECT COUNT(DISTINCT codigo_cpc)
            FROM observaciones
            """
        ).fetchone()[0]
    )

    origenes = int(
        conexion.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    codigo_departamento_origen,
                    codigo_municipio_pais_origen
                FROM observaciones
            )
            """
        ).fetchone()[0]
    )

    cantidad_total = Decimal("0")

    for (cantidad_texto,) in conexion.execute(
        """
        SELECT cantidad_kg
        FROM observaciones
        """
    ):
        cantidad_total += Decimal(cantidad_texto)

    archivos_fuente = [
        str(fila_archivo[0])
        for fila_archivo in conexion.execute(
            """
            SELECT DISTINCT archivo_fuente
            FROM observaciones
            ORDER BY archivo_fuente
            """
        )
    ]

    return (
        fecha_minima,
        fecha_maxima,
        observaciones,
        registros_fuente,
        productos,
        mercados,
        cpc,
        origenes,
        cantidad_total,
        archivos_fuente,
    )


def _escribir_manifiesto(
    *,
    ruta: Path,
    nombre: str,
    fecha_minima: str,
    fecha_maxima: str,
    observaciones: int,
    registros_fuente: int,
    productos: int,
    mercados: int,
    cpc: int,
    origenes: int,
    cantidad_total_kg: Decimal,
    archivos_fuente: list[str],
    sha256_datos: str,
) -> None:
    """Escribe el manifiesto reproducible de la serie."""
    manifiesto = {
        "formato": "vigia-abastecimiento-diario-sipsa-v1",
        "fuente": "SIPSA-DANE",
        "nombre": nombre,
        "granularidad": (
            "fecha+producto+mercado_destino+departamento_origen+municipio_pais_origen"
        ),
        "agregacion": "SUM(cantidad_kg)",
        "fecha_minima": fecha_minima,
        "fecha_maxima": fecha_maxima,
        "observaciones": observaciones,
        "registros_fuente": registros_fuente,
        "productos": productos,
        "mercados": mercados,
        "cpc": cpc,
        "origenes": origenes,
        "cantidad_total_kg": str(cantidad_total_kg),
        "archivos_fuente": archivos_fuente,
        "sha256_datos": sha256_datos,
    }

    temporal = Path(f"{ruta}.parcial")

    try:
        temporal.write_text(
            json.dumps(
                manifiesto,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        os.replace(
            temporal,
            ruta,
        )

    except OSError as exc:
        temporal.unlink(missing_ok=True)

        raise ErrorPersistenciaAbastecimientoSipsa(
            f"No fue posible escribir el manifiesto {ruta}: {exc}"
        ) from exc


def persistir_abastecimiento_diario_sipsa(
    observaciones: Iterable[ObservacionAbastecimientoDiarioSipsa],
    *,
    directorio: Path,
    nombre: str = "abastecimiento_diario_2026",
) -> ResultadoPersistenciaAbastecimiento:
    """
    Persiste una serie diaria SIPSA_A de manera reproducible.

    La función acepta cualquier orden de entrada. SQLite impone el orden
    canónico antes de escribir el artefacto final.
    """
    _validar_nombre_base(nombre)

    directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_datos = directorio / f"{nombre}.csv.gz"

    ruta_manifiesto = directorio / f"{nombre}.json"

    ruta_bd = directorio / f".{nombre}.persistencia.sqlite"

    conexion = _crear_base_temporal(ruta_bd)

    try:
        total_insertado = _insertar_observaciones(
            conexion,
            observaciones,
        )

        (
            fecha_minima,
            fecha_maxima,
            observaciones_totales,
            registros_fuente,
            productos,
            mercados,
            cpc,
            origenes,
            cantidad_total_kg,
            archivos_fuente,
        ) = _obtener_estadisticas(conexion)

        if total_insertado != observaciones_totales:
            raise ErrorPersistenciaAbastecimientoSipsa(
                "La cardinalidad persistida no coincide con la cardinalidad recibida."
            )

        _escribir_csv_gzip(
            conexion,
            ruta_datos,
        )

        sha256_datos = _sha256(ruta_datos)

        _escribir_manifiesto(
            ruta=ruta_manifiesto,
            nombre=nombre,
            fecha_minima=fecha_minima,
            fecha_maxima=fecha_maxima,
            observaciones=observaciones_totales,
            registros_fuente=registros_fuente,
            productos=productos,
            mercados=mercados,
            cpc=cpc,
            origenes=origenes,
            cantidad_total_kg=cantidad_total_kg,
            archivos_fuente=archivos_fuente,
            sha256_datos=sha256_datos,
        )

        return ResultadoPersistenciaAbastecimiento(
            ruta_datos=ruta_datos,
            ruta_manifiesto=ruta_manifiesto,
            observaciones=observaciones_totales,
            registros_fuente=registros_fuente,
            fecha_minima=fecha_minima,
            fecha_maxima=fecha_maxima,
            productos=productos,
            mercados=mercados,
            cpc=cpc,
            origenes=origenes,
            cantidad_total_kg=cantidad_total_kg,
            sha256_datos=sha256_datos,
        )

    finally:
        conexion.close()

        ruta_bd.unlink(missing_ok=True)

        for sufijo in (
            "-journal",
            "-shm",
            "-wal",
        ):
            Path(f"{ruta_bd}{sufijo}").unlink(missing_ok=True)
