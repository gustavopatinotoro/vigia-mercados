"""
Persistencia reproducible de series históricas mensuales SIPSA_P.

Las observaciones se almacenan en un CSV.GZ determinista acompañado de:

- un CSV.GZ independiente con las observaciones pertenecientes a claves
  conflictivas;
- un manifiesto JSON con métricas, rango temporal y hashes SHA-256.

La persistencia conserva todas las observaciones de la fuente. No deduplica,
promedia ni selecciona registros conflictivos.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from vigia.dominio.sipsa import (
    ObservacionPrecioMensualSipsa,
    detectar_conflictos_precios_mensuales,
)


@dataclass(frozen=True, slots=True)
class ResultadoPersistenciaPreciosMensuales:
    """Resultado verificable de persistir la serie histórica SIPSA_P."""

    ruta_datos: Path
    ruta_conflictos: Path
    ruta_manifiesto: Path
    observaciones: int
    claves_candidatas: int
    conflictos: int
    observaciones_conflictivas: int
    observaciones_excedentes: int
    sha256_datos: str
    sha256_conflictos: str


_CAMPOS_DATOS = (
    "fecha_mes",
    "producto",
    "mercado",
    "grupo",
    "codigo_cpc",
    "precio_promedio_kg",
    "fuente",
    "archivo_fuente",
)

_CAMPOS_CONFLICTOS = (
    "fecha_mes",
    "producto",
    "mercado",
    "numero_observaciones_conflicto",
    "grupo",
    "codigo_cpc",
    "precio_promedio_kg",
    "fuente",
    "archivo_fuente",
)


def _validar_nombre(nombre: str) -> str:
    """Valida un nombre base seguro para los artefactos."""
    nombre_limpio = nombre.strip()

    if not nombre_limpio:
        raise ValueError("nombre no puede estar vacío.")

    if Path(nombre_limpio).name != nombre_limpio:
        raise ValueError("nombre debe ser un nombre base, no una ruta.")

    return nombre_limpio


def _clave_orden(
    observacion: ObservacionPrecioMensualSipsa,
) -> tuple[str, str, str, str, str, str, str, str]:
    """Define un orden total y reproducible para las observaciones."""
    return (
        observacion.fecha_mes.isoformat(),
        observacion.producto,
        observacion.mercado,
        observacion.grupo,
        observacion.codigo_cpc or "",
        format(
            observacion.precio_promedio_kg,
            "f",
        ),
        observacion.fuente,
        observacion.archivo_fuente,
    )


def _fila_datos(
    observacion: ObservacionPrecioMensualSipsa,
) -> tuple[str, ...]:
    """Convierte una observación en una fila CSV estable."""
    return (
        observacion.fecha_mes.isoformat(),
        observacion.producto,
        observacion.mercado,
        observacion.grupo,
        observacion.codigo_cpc or "",
        format(
            observacion.precio_promedio_kg,
            "f",
        ),
        observacion.fuente,
        observacion.archivo_fuente,
    )


def _sha256_archivo(ruta: Path) -> str:
    """Calcula SHA-256 sin cargar el artefacto completo en memoria."""
    resumen = hashlib.sha256()

    with ruta.open("rb") as archivo:
        while bloque := archivo.read(1024 * 1024):
            resumen.update(bloque)

    return resumen.hexdigest()


def _escribir_csv_gzip(
    ruta: Path,
    *,
    encabezado: tuple[str, ...],
    filas: Iterable[tuple[str, ...]],
) -> None:
    """Escribe un CSV.GZ byte a byte reproducible."""
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_temporal = ruta.with_name(f".{ruta.name}.parcial")

    try:
        with (
            ruta_temporal.open("wb") as archivo_binario,
            gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=archivo_binario,
                mtime=0,
            ) as archivo_gzip,
            io.TextIOWrapper(
                archivo_gzip,
                encoding="utf-8",
                newline="",
            ) as texto,
        ):
            escritor = csv.writer(
                texto,
                lineterminator="\n",
            )

            escritor.writerow(encabezado)

            escritor.writerows(filas)

        os.replace(
            ruta_temporal,
            ruta,
        )

    except BaseException:
        ruta_temporal.unlink(missing_ok=True)
        raise


def _escribir_json(
    ruta: Path,
    contenido: dict[str, object],
) -> None:
    """Escribe un manifiesto JSON determinista mediante reemplazo atómico."""
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_temporal = ruta.with_name(f".{ruta.name}.parcial")

    texto = json.dumps(
        contenido,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    try:
        ruta_temporal.write_text(
            f"{texto}\n",
            encoding="utf-8",
        )

        os.replace(
            ruta_temporal,
            ruta,
        )

    except BaseException:
        ruta_temporal.unlink(missing_ok=True)
        raise


def persistir_precios_mensuales_sipsa(
    observaciones: Iterable[ObservacionPrecioMensualSipsa],
    *,
    directorio: Path,
    nombre: str = "precios_mensuales_2013_2024",
) -> ResultadoPersistenciaPreciosMensuales:
    """
    Persiste una serie histórica SIPSA_P de forma reproducible.

    Todas las observaciones se conservan en el artefacto principal. Las claves
    candidatas repetidas se registran adicionalmente en un artefacto de
    conflictos para impedir que la anomalía de fuente quede oculta.
    """
    nombre_validado = _validar_nombre(nombre)

    registros = sorted(
        observaciones,
        key=_clave_orden,
    )

    if not registros:
        raise ValueError("Se requiere al menos una observación de precio.")

    conflictos = detectar_conflictos_precios_mensuales(registros)

    claves_candidatas = {observacion.clave_natural for observacion in registros}

    observaciones_conflictivas = sum(len(conflicto.observaciones) for conflicto in conflictos)

    observaciones_excedentes = sum(len(conflicto.observaciones) - 1 for conflicto in conflictos)

    ruta_datos = directorio / f"{nombre_validado}.csv.gz"

    ruta_conflictos = directorio / f"{nombre_validado}_conflictos.csv.gz"

    ruta_manifiesto = directorio / f"{nombre_validado}.json"

    _escribir_csv_gzip(
        ruta_datos,
        encabezado=_CAMPOS_DATOS,
        filas=(_fila_datos(observacion) for observacion in registros),
    )

    filas_conflicto: list[tuple[str, ...]] = []

    for conflicto in conflictos:
        cantidad = str(len(conflicto.observaciones))

        for observacion in sorted(
            conflicto.observaciones,
            key=_clave_orden,
        ):
            filas_conflicto.append(
                (
                    observacion.fecha_mes.isoformat(),
                    observacion.producto,
                    observacion.mercado,
                    cantidad,
                    observacion.grupo,
                    observacion.codigo_cpc or "",
                    format(
                        observacion.precio_promedio_kg,
                        "f",
                    ),
                    observacion.fuente,
                    observacion.archivo_fuente,
                )
            )

    _escribir_csv_gzip(
        ruta_conflictos,
        encabezado=_CAMPOS_CONFLICTOS,
        filas=filas_conflicto,
    )

    sha256_datos = _sha256_archivo(ruta_datos)

    sha256_conflictos = _sha256_archivo(ruta_conflictos)

    fechas = [observacion.fecha_mes for observacion in registros]

    productos = {observacion.producto for observacion in registros}

    mercados = {observacion.mercado for observacion in registros}

    grupos = {observacion.grupo for observacion in registros}

    codigos_cpc = {
        observacion.codigo_cpc for observacion in registros if observacion.codigo_cpc is not None
    }

    archivos_fuente = sorted({observacion.archivo_fuente for observacion in registros})

    manifiesto: dict[str, object] = {
        "formato": "vigia-precios-mensuales-sipsa-v1",
        "fuente": "SIPSA-DANE",
        "nombre": nombre_validado,
        "observaciones": len(registros),
        "claves_candidatas": len(claves_candidatas),
        "conflictos": len(conflictos),
        "observaciones_conflictivas": (observaciones_conflictivas),
        "observaciones_excedentes": (observaciones_excedentes),
        "fecha_minima": min(fechas).isoformat(),
        "fecha_maxima": max(fechas).isoformat(),
        "productos": len(productos),
        "mercados": len(mercados),
        "grupos_observados": len(grupos),
        "codigos_cpc_observados": len(codigos_cpc),
        "archivos_fuente": archivos_fuente,
        "sha256_datos": sha256_datos,
        "sha256_conflictos": (sha256_conflictos),
    }

    _escribir_json(
        ruta_manifiesto,
        manifiesto,
    )

    return ResultadoPersistenciaPreciosMensuales(
        ruta_datos=ruta_datos,
        ruta_conflictos=ruta_conflictos,
        ruta_manifiesto=ruta_manifiesto,
        observaciones=len(registros),
        claves_candidatas=len(claves_candidatas),
        conflictos=len(conflictos),
        observaciones_conflictivas=(observaciones_conflictivas),
        observaciones_excedentes=(observaciones_excedentes),
        sha256_datos=sha256_datos,
        sha256_conflictos=sha256_conflictos,
    )
