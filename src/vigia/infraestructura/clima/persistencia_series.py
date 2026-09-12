"""
Persistencia reproducible de series climáticas territoriales horarias.

Los datos se almacenan en CSV comprimido con gzip determinista y se
acompañan de un manifiesto JSON que conserva metadatos operativos y la
huella SHA-256 del artefacto generado.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from vigia.dominio.clima import (
    ObservacionClimaticaTerritorialHoraria,
)


@dataclass(frozen=True, slots=True)
class ResultadoPersistenciaSerieClimatica:
    """Resultado verificable de una operación de persistencia."""

    ruta_datos: Path
    ruta_manifiesto: Path
    sha256: str
    registros: int


def persistir_series_territoriales_horarias(
    observaciones: Iterable[ObservacionClimaticaTerritorialHoraria],
    *,
    directorio: Path,
    nombre_base: str,
    fuente: str = "IDEAM",
) -> ResultadoPersistenciaSerieClimatica:
    """
    Persiste una serie territorial horaria y genera su manifiesto.

    El artefacto gzip es determinista: para el mismo contenido lógico
    debe producir exactamente los mismos bytes y el mismo SHA-256.
    """
    if not nombre_base.strip():
        raise ValueError("nombre_base no puede estar vacío.")

    if not fuente.strip():
        raise ValueError("fuente no puede estar vacía.")

    registros = tuple(
        sorted(
            observaciones,
            key=lambda observacion: (
                observacion.codigo_divipola,
                observacion.variable.value,
                observacion.fecha_hora,
            ),
        )
    )

    directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_datos = directorio / f"{nombre_base}.csv.gz"
    ruta_manifiesto = directorio / f"{nombre_base}.json"

    _escribir_csv_determinista(
        ruta=ruta_datos,
        observaciones=registros,
    )

    sha256 = _calcular_sha256(ruta_datos)

    _escribir_manifiesto(
        ruta=ruta_manifiesto,
        nombre_base=nombre_base,
        fuente=fuente,
        observaciones=registros,
        sha256=sha256,
    )

    return ResultadoPersistenciaSerieClimatica(
        ruta_datos=ruta_datos,
        ruta_manifiesto=ruta_manifiesto,
        sha256=sha256,
        registros=len(registros),
    )


def _escribir_csv_determinista(
    *,
    ruta: Path,
    observaciones: tuple[ObservacionClimaticaTerritorialHoraria, ...],
) -> None:
    """
    Escribe CSV gzip de forma determinista.

    mtime=0 evita que la fecha de generación modifique los bytes del gzip.
    filename="" evita incorporar el nombre físico del archivo en su cabecera.
    """
    with (
        ruta.open("wb") as archivo_binario,
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
        ) as archivo_texto,
    ):
        escritor = csv.writer(
            archivo_texto,
            lineterminator="\n",
        )

        escritor.writerow(
            (
                "codigo_divipola",
                "variable",
                "fecha_hora",
                "valor",
                "unidad",
                "estaciones_utilizadas",
                "observaciones_fuente",
            )
        )

        for observacion in observaciones:
            escritor.writerow(
                (
                    observacion.codigo_divipola,
                    observacion.variable.value,
                    observacion.fecha_hora.isoformat(),
                    str(observacion.valor),
                    observacion.unidad,
                    observacion.estaciones_utilizadas,
                    observacion.observaciones_fuente,
                )
            )


def _escribir_manifiesto(
    *,
    ruta: Path,
    nombre_base: str,
    fuente: str,
    observaciones: tuple[ObservacionClimaticaTerritorialHoraria, ...],
    sha256: str,
) -> None:
    """Escribe metadatos suficientes para auditar el artefacto."""
    territorios = {observacion.codigo_divipola for observacion in observaciones}

    variables = sorted({observacion.variable.value for observacion in observaciones})

    fechas = [observacion.fecha_hora for observacion in observaciones]

    manifiesto: dict[str, object] = {
        "formato": "vigia-serie-climatica-territorial-horaria-v1",
        "nombre": nombre_base,
        "fuente": fuente,
        "registros": len(observaciones),
        "territorios": len(territorios),
        "variables": variables,
        "sha256_datos": sha256,
    }

    if fechas:
        manifiesto["fecha_hora_minima"] = min(fechas).isoformat()
        manifiesto["fecha_hora_maxima"] = max(fechas).isoformat()
    else:
        manifiesto["fecha_hora_minima"] = None
        manifiesto["fecha_hora_maxima"] = None

    contenido = json.dumps(
        manifiesto,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    ruta.write_text(
        contenido + "\n",
        encoding="utf-8",
    )


def _calcular_sha256(
    ruta: Path,
) -> str:
    """Calcula SHA-256 mediante lectura incremental."""
    digest = hashlib.sha256()

    with ruta.open("rb") as archivo:
        while bloque := archivo.read(1024 * 1024):
            digest.update(bloque)

    return digest.hexdigest()
