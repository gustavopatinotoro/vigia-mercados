"""
Caso de uso para construir la serie histórica mensual de precios SIPSA_P.

Coordina:

- descubrimiento de archivos oficiales ZIP;
- extracción del único CSV de cada fuente;
- detección automática del perfil histórico;
- parsing al contrato canónico;
- detección de conflictos;
- persistencia reproducible.

No corrige, deduplica ni promedia observaciones conflictivas.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

from vigia.dominio.sipsa import (
    ObservacionPrecioMensualSipsa,
    detectar_conflictos_precios_mensuales,
)
from vigia.infraestructura.sipsa import (
    PerfilEsquemaPrecioMensualSipsa,
    detectar_perfil_precios_mensuales_sipsa,
    parsear_precios_mensuales_sipsa,
)
from vigia.infraestructura.sipsa.persistencia_precios_mensuales import (
    ResultadoPersistenciaPreciosMensuales,
    persistir_precios_mensuales_sipsa,
)


class ErrorGeneracionPreciosMensuales(RuntimeError):
    """Error producido durante la generación histórica SIPSA_P."""


@dataclass(frozen=True, slots=True)
class EstadisticasArchivoPrecioMensual:
    """Estadísticas de una fuente histórica SIPSA_P procesada."""

    periodo: str
    archivo_zip: str
    archivo_csv: str
    perfil: str
    observaciones: int
    conflictos: int


@dataclass(frozen=True, slots=True)
class ResultadoGeneracionPreciosMensuales:
    """Resultado completo del caso de uso histórico SIPSA_P."""

    estadisticas_archivos: tuple[
        EstadisticasArchivoPrecioMensual,
        ...,
    ]
    observaciones: int
    claves_candidatas: int
    conflictos: int
    observaciones_conflictivas: int
    observaciones_excedentes: int
    persistencia: ResultadoPersistenciaPreciosMensuales


def _leer_unico_csv_zip(
    ruta_zip: Path,
) -> tuple[str, bytes]:
    """Extrae el único CSV contenido en un ZIP SIPSA_P."""
    if not ruta_zip.exists():
        raise ErrorGeneracionPreciosMensuales(f"No existe el archivo esperado: {ruta_zip}")

    if not ruta_zip.is_file():
        raise ErrorGeneracionPreciosMensuales(f"La ruta no corresponde a un archivo: {ruta_zip}")

    try:
        with zipfile.ZipFile(ruta_zip) as archivo_zip:
            csvs = [nombre for nombre in archivo_zip.namelist() if nombre.lower().endswith(".csv")]

            if len(csvs) != 1:
                raise ErrorGeneracionPreciosMensuales(
                    f"{ruta_zip.name} debe contener exactamente un CSV; encontrados={csvs}"
                )

            nombre_csv = csvs[0]
            contenido = archivo_zip.read(nombre_csv)

    except zipfile.BadZipFile as exc:
        raise ErrorGeneracionPreciosMensuales(
            f"El archivo no es un ZIP válido: {ruta_zip}"
        ) from exc

    return nombre_csv, contenido


def _resolver_archivos_historicos(
    directorio_fuentes: Path,
) -> tuple[
    tuple[str, Path],
    ...,
]:
    """Resuelve los ZIP oficiales requeridos para 2013-2024."""
    if not directorio_fuentes.exists():
        raise ErrorGeneracionPreciosMensuales(
            f"No existe el directorio de fuentes: {directorio_fuentes}"
        )

    if not directorio_fuentes.is_dir():
        raise ErrorGeneracionPreciosMensuales(
            f"La ruta de fuentes no es un directorio: {directorio_fuentes}"
        )

    archivos: list[tuple[str, Path]] = []

    ruta_inicial = directorio_fuentes / "BaseDatos-SIPSA_P-Mensual-2013_2017.zip"

    if not ruta_inicial.exists():
        raise ErrorGeneracionPreciosMensuales(
            f"Falta la fuente histórica 2013-2017: {ruta_inicial}"
        )

    archivos.append(
        (
            "2013-2017",
            ruta_inicial,
        )
    )

    for anio in range(2018, 2025):
        candidatos = sorted(directorio_fuentes.glob(f"BaseDatos-SIPSA_P-Mensual-{anio}*.zip"))

        if len(candidatos) != 1:
            raise ErrorGeneracionPreciosMensuales(
                f"{anio}: se esperaba exactamente un ZIP oficial; encontrados={candidatos}"
            )

        archivos.append(
            (
                str(anio),
                candidatos[0],
            )
        )

    return tuple(archivos)


def _procesar_archivo(
    *,
    periodo: str,
    ruta_zip: Path,
) -> tuple[
    list[ObservacionPrecioMensualSipsa],
    EstadisticasArchivoPrecioMensual,
]:
    """Procesa una fuente histórica SIPSA_P completa."""
    nombre_csv, contenido = _leer_unico_csv_zip(ruta_zip)

    try:
        perfil: PerfilEsquemaPrecioMensualSipsa = detectar_perfil_precios_mensuales_sipsa(contenido)

        observaciones = list(
            parsear_precios_mensuales_sipsa(
                contenido,
                archivo_fuente=nombre_csv,
            )
        )

    except (ValueError, RuntimeError) as exc:
        raise ErrorGeneracionPreciosMensuales(
            f"No fue posible procesar {ruta_zip.name}: {exc}"
        ) from exc

    conflictos = detectar_conflictos_precios_mensuales(observaciones)

    estadisticas = EstadisticasArchivoPrecioMensual(
        periodo=periodo,
        archivo_zip=ruta_zip.name,
        archivo_csv=nombre_csv,
        perfil=perfil.nombre,
        observaciones=len(observaciones),
        conflictos=len(conflictos),
    )

    return observaciones, estadisticas


def generar_serie_historica_precios_sipsa(
    *,
    directorio_fuentes: Path,
    directorio_salida: Path,
    nombre: str = "precios_mensuales_2013_2024",
) -> ResultadoGeneracionPreciosMensuales:
    """
    Genera la serie mensual SIPSA_P completa para 2013-2024.

    Los conflictos de clave candidata se conservan en la serie principal y
    además se persisten en un artefacto independiente de auditoría.
    """
    fuentes = _resolver_archivos_historicos(directorio_fuentes)

    todas_observaciones: list[ObservacionPrecioMensualSipsa] = []

    estadisticas: list[EstadisticasArchivoPrecioMensual] = []

    for periodo, ruta_zip in fuentes:
        observaciones, estadistica = _procesar_archivo(
            periodo=periodo,
            ruta_zip=ruta_zip,
        )

        todas_observaciones.extend(observaciones)

        estadisticas.append(estadistica)

    if not todas_observaciones:
        raise ErrorGeneracionPreciosMensuales("Las fuentes SIPSA_P no produjeron observaciones.")

    conflictos = detectar_conflictos_precios_mensuales(todas_observaciones)

    claves_candidatas = {observacion.clave_natural for observacion in todas_observaciones}

    observaciones_conflictivas = sum(len(conflicto.observaciones) for conflicto in conflictos)

    observaciones_excedentes = sum(len(conflicto.observaciones) - 1 for conflicto in conflictos)

    persistencia = persistir_precios_mensuales_sipsa(
        todas_observaciones,
        directorio=directorio_salida,
        nombre=nombre,
    )

    return ResultadoGeneracionPreciosMensuales(
        estadisticas_archivos=tuple(estadisticas),
        observaciones=len(todas_observaciones),
        claves_candidatas=len(claves_candidatas),
        conflictos=len(conflictos),
        observaciones_conflictivas=(observaciones_conflictivas),
        observaciones_excedentes=(observaciones_excedentes),
        persistencia=persistencia,
    )
