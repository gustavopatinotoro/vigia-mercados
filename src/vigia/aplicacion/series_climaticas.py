"""
Caso de uso para generar series climáticas territoriales horarias.

Orquesta la adquisición de observaciones IDEAM, su normalización,
consolidación por estación, agregación temporal horaria,
territorialización DIVIPOLA y agregación territorial final.

No contiene lógica de interfaz de línea de comandos.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from vigia.dominio.clima import (
    ObservacionClimaticaTerritorialHoraria,
    VariableClimatica,
    agregar_observaciones_horarias_estacion,
    agregar_observaciones_territoriales_horarias,
    consolidar_observaciones_estacion,
)
from vigia.infraestructura.clima import (
    ResultadoPersistenciaSerieClimatica,
    persistir_series_territoriales_horarias,
)
from vigia.infraestructura.ideam import (
    ClienteIdeam,
    ConsultaSocrata,
    normalizar_observaciones_ideam,
    parsear_observaciones_ideam,
)
from vigia.infraestructura.territorio import (
    construir_mapa_estaciones_ideam,
)

DATASET_PRECIPITACION = "s54a-sgyg"
DATASET_TEMPERATURA = "sbwg-7ju4"

TAMANO_PAGINA_PREDETERMINADO = 5000
TIMEOUT_PREDETERMINADO = 120.0


class ErrorGeneracionSeriesClimaticas(RuntimeError):
    """Error al generar series climáticas territoriales."""


@dataclass(frozen=True, slots=True)
class EstadisticasVariableClimatica:
    """Trazabilidad cuantitativa de una variable durante el pipeline."""

    variable: VariableClimatica
    registros_descargados: int
    observaciones_unicas: int
    observaciones_consolidadas: int
    observaciones_estacion_hora: int
    observaciones_territorio_hora: int
    estaciones_con_datos: int
    territorios_con_datos: int


@dataclass(frozen=True, slots=True)
class ResultadoGeneracionSeriesClimaticas:
    """Resultado completo del caso de uso de generación climática."""

    inicio: datetime
    fin: datetime
    estaciones_catalogo: int
    estaciones_territorializadas: int
    estaciones_no_territorializadas: int
    estadisticas: tuple[EstadisticasVariableClimatica, ...]
    persistencia: ResultadoPersistenciaSerieClimatica


@dataclass(frozen=True, slots=True)
class _ConfiguracionDataset:
    """Configuración interna de una variable climática IDEAM."""

    nombre: str
    dataset_id: str
    variable: VariableClimatica


_DATASETS = (
    _ConfiguracionDataset(
        nombre="precipitacion",
        dataset_id=DATASET_PRECIPITACION,
        variable=VariableClimatica.PRECIPITACION,
    ),
    _ConfiguracionDataset(
        nombre="temperatura",
        dataset_id=DATASET_TEMPERATURA,
        variable=VariableClimatica.TEMPERATURA,
    ),
)


def generar_series_climaticas_territoriales(
    *,
    inicio: datetime,
    fin: datetime,
    directorio_salida: Path,
    nombre_base: str | None = None,
    tamano_pagina: int = TAMANO_PAGINA_PREDETERMINADO,
    timeout_segundos: float = TIMEOUT_PREDETERMINADO,
    informar: Callable[[str], None] | None = None,
) -> ResultadoGeneracionSeriesClimaticas:
    """
    Genera y persiste series climáticas territoriales horarias.

    El intervalo utiliza semántica [inicio, fin): inicio incluido y fin
    excluido.
    """
    _validar_parametros(
        inicio=inicio,
        fin=fin,
        tamano_pagina=tamano_pagina,
        timeout_segundos=timeout_segundos,
    )

    emitir = informar or (lambda _: None)

    emitir("Construyendo mapa territorial del catálogo IDEAM completo...")

    resultado_mapa = construir_mapa_estaciones_ideam(
        timeout_segundos=timeout_segundos,
        timeout_mgn_segundos=timeout_segundos,
    )

    mapa = resultado_mapa.divipola_por_estacion

    series_territoriales: list[ObservacionClimaticaTerritorialHoraria] = []

    estadisticas: list[EstadisticasVariableClimatica] = []

    cliente = ClienteIdeam()

    for configuracion in _DATASETS:
        emitir(f"Procesando {configuracion.nombre}...")

        registros = _descargar_intervalo(
            cliente=cliente,
            dataset_id=configuracion.dataset_id,
            inicio=inicio,
            fin=fin,
            tamano_pagina=tamano_pagina,
            timeout_segundos=timeout_segundos,
            informar=emitir,
        )

        observaciones = tuple(
            parsear_observaciones_ideam(
                registros,
                variable=configuracion.variable,
            )
        )

        normalizadas = normalizar_observaciones_ideam(observaciones)

        consolidadas = consolidar_observaciones_estacion(normalizadas.observaciones)

        horarias_estacion = agregar_observaciones_horarias_estacion(consolidadas)

        codigos_sin_territorio = sorted(
            {
                observacion.codigo_estacion
                for observacion in horarias_estacion
                if observacion.codigo_estacion not in mapa
            }
        )

        if codigos_sin_territorio:
            raise ErrorGeneracionSeriesClimaticas(
                "Existen estaciones con observaciones horarias "
                "sin correspondencia territorial DIVIPOLA: "
                f"{codigos_sin_territorio!r}."
            )

        horarias_territorio = agregar_observaciones_territoriales_horarias(
            horarias_estacion,
            divipola_por_estacion=mapa,
        )

        series_territoriales.extend(horarias_territorio)

        estaciones = {observacion.codigo_estacion for observacion in horarias_estacion}

        territorios = {observacion.codigo_divipola for observacion in horarias_territorio}

        estadistica = EstadisticasVariableClimatica(
            variable=configuracion.variable,
            registros_descargados=len(registros),
            observaciones_unicas=len(normalizadas.observaciones),
            observaciones_consolidadas=len(consolidadas),
            observaciones_estacion_hora=len(horarias_estacion),
            observaciones_territorio_hora=len(horarias_territorio),
            estaciones_con_datos=len(estaciones),
            territorios_con_datos=len(territorios),
        )

        estadisticas.append(estadistica)

        emitir(
            f"{configuracion.nombre}: "
            f"{estadistica.observaciones_territorio_hora} "
            "registros territorio-hora."
        )

    nombre = (
        nombre_base
        if nombre_base is not None
        else _nombre_base_predeterminado(
            inicio=inicio,
            fin=fin,
        )
    )

    persistencia = persistir_series_territoriales_horarias(
        series_territoriales,
        directorio=directorio_salida,
        nombre_base=nombre,
        fuente="IDEAM",
    )

    emitir(f"Persistidos {persistencia.registros} registros.")

    return ResultadoGeneracionSeriesClimaticas(
        inicio=inicio,
        fin=fin,
        estaciones_catalogo=resultado_mapa.estaciones_totales,
        estaciones_territorializadas=resultado_mapa.estaciones_resueltas,
        estaciones_no_territorializadas=len(resultado_mapa.estaciones_no_resueltas),
        estadisticas=tuple(estadisticas),
        persistencia=persistencia,
    )


def _descargar_intervalo(
    *,
    cliente: ClienteIdeam,
    dataset_id: str,
    inicio: datetime,
    fin: datetime,
    tamano_pagina: int,
    timeout_segundos: float,
    informar: Callable[[str], None],
) -> list[dict[str, object]]:
    """
    Descarga un intervalo mediante ventanas horarias y paginación.

    La partición temporal reduce la carga impuesta a Socrata y evita
    consultas nacionales masivas que previamente produjeron HTTP 500.
    """
    registros_totales: list[dict[str, object]] = []

    cursor = inicio

    while cursor < fin:
        siguiente = min(
            cursor + timedelta(hours=1),
            fin,
        )

        desplazamiento = 0

        filtro = (
            f"fechaobservacion >= '{_fecha_socrata(cursor)}' "
            f"AND fechaobservacion < '{_fecha_socrata(siguiente)}'"
        )

        registros_ventana = 0

        while True:
            pagina = cliente.consultar(
                dataset_id,
                consulta=ConsultaSocrata(
                    limite=tamano_pagina,
                    desplazamiento=desplazamiento,
                    filtro=filtro,
                    orden=("fechaobservacion,codigoestacion,codigosensor"),
                ),
                timeout_segundos=timeout_segundos,
            )

            registros_totales.extend(pagina)

            registros_ventana += len(pagina)

            if len(pagina) < tamano_pagina:
                break

            desplazamiento += tamano_pagina

        informar(f"{cursor.isoformat()} → {siguiente.isoformat()} | {registros_ventana} registros")

        cursor = siguiente

    return registros_totales


def _fecha_socrata(
    fecha: datetime,
) -> str:
    """Serializa datetime para filtros temporales Socrata."""
    return fecha.strftime("%Y-%m-%dT%H:%M:%S.000")


def _nombre_base_predeterminado(
    *,
    inicio: datetime,
    fin: datetime,
) -> str:
    """Construye un nombre estable para el intervalo generado."""
    if (
        inicio.minute == 0
        and inicio.second == 0
        and inicio.microsecond == 0
        and fin - inicio == timedelta(days=1)
        and inicio.hour == 0
    ):
        return f"series_territoriales_horarias_{inicio.date().isoformat()}"

    return (
        "series_territoriales_horarias_"
        f"{inicio.strftime('%Y%m%dT%H%M%S')}_"
        f"{fin.strftime('%Y%m%dT%H%M%S')}"
    )


def _validar_parametros(
    *,
    inicio: datetime,
    fin: datetime,
    tamano_pagina: int,
    timeout_segundos: float,
) -> None:
    """Valida precondiciones del caso de uso."""
    if fin <= inicio:
        raise ValueError("fin debe ser posterior a inicio.")

    if tamano_pagina <= 0:
        raise ValueError("tamano_pagina debe ser mayor que cero.")

    if timeout_segundos <= 0:
        raise ValueError("timeout_segundos debe ser mayor que cero.")
