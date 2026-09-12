"""
Parser unificado del histórico mensual SIPSA_P.

La publicación histórica del DANE presenta varios esquemas entre 2013 y 2024.
Este módulo detecta explícitamente el perfil de cada CSV y normaliza sus
registros al contrato analítico común ``ObservacionPrecioMensualSipsa``.

No deduplica observaciones, no corrige clasificaciones y no resuelve
conflictos de fuente. Su responsabilidad termina en la interpretación fiel
del archivo publicado.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from vigia.dominio.sipsa import ObservacionPrecioMensualSipsa


class ErrorParserPreciosMensualesHistoricoSipsa(RuntimeError):
    """Error producido al interpretar un histórico mensual SIPSA_P."""


@dataclass(frozen=True, slots=True)
class PerfilEsquemaPrecioMensualSipsa:
    """Describe una versión conocida del esquema histórico SIPSA_P."""

    nombre: str
    codificacion: str
    columnas: tuple[str, ...]
    campo_mercado: str
    campo_precio: str
    fecha_abreviada: bool
    precio_con_separador_miles: bool
    campo_cpc: str | None = None
    permite_columnas_vacias_extra: bool = False


PERFIL_2013_2018 = PerfilEsquemaPrecioMensualSipsa(
    nombre="2013-2018",
    codificacion="latin-1",
    columnas=(
        "Fecha",
        "Grupo",
        "Producto",
        "Fuente",
        "Precio",
    ),
    campo_mercado="Fuente",
    campo_precio="Precio",
    fecha_abreviada=False,
    precio_con_separador_miles=False,
)

PERFIL_2019 = PerfilEsquemaPrecioMensualSipsa(
    nombre="2019",
    codificacion="latin-1",
    columnas=(
        "Fecha",
        "Grupo",
        "Producto",
        "Fuente",
        "Precio_por_kilogramo",
    ),
    campo_mercado="Fuente",
    campo_precio="Precio_por_kilogramo",
    fecha_abreviada=False,
    precio_con_separador_miles=False,
)

PERFIL_2020 = PerfilEsquemaPrecioMensualSipsa(
    nombre="2020",
    codificacion="latin-1",
    columnas=(
        "Fecha",
        "Grupo",
        "Producto",
        "Mercado",
        "Precio_por_kilogramo",
    ),
    campo_mercado="Mercado",
    campo_precio="Precio_por_kilogramo",
    fecha_abreviada=False,
    precio_con_separador_miles=False,
)

PERFIL_2021 = PerfilEsquemaPrecioMensualSipsa(
    nombre="2021",
    codificacion="latin-1",
    columnas=(
        "Fecha",
        "Grupo",
        "Producto",
        "Mercado",
        "Precio_promedio_por_kilogramo",
    ),
    campo_mercado="Mercado",
    campo_precio="Precio_promedio_por_kilogramo",
    fecha_abreviada=False,
    precio_con_separador_miles=False,
)

PERFIL_2022_2023 = PerfilEsquemaPrecioMensualSipsa(
    nombre="2022-2023",
    codificacion="latin-1",
    columnas=(
        "Fecha",
        "Grupo",
        "Producto",
        "Mercado",
        "Precio promedio por kilogramo*",
    ),
    campo_mercado="Mercado",
    campo_precio="Precio promedio por kilogramo*",
    fecha_abreviada=True,
    precio_con_separador_miles=True,
    permite_columnas_vacias_extra=True,
)

PERFIL_2024 = PerfilEsquemaPrecioMensualSipsa(
    nombre="2024",
    codificacion="utf-8-sig",
    columnas=(
        "Fecha",
        "Grupo",
        "Producto",
        "CODIGO_CPC_AC",
        "Mercado",
        "Precio promedio por kilogramo*",
    ),
    campo_mercado="Mercado",
    campo_precio="Precio promedio por kilogramo*",
    fecha_abreviada=True,
    precio_con_separador_miles=True,
    campo_cpc="CODIGO_CPC_AC",
)

PERFILES_CONOCIDOS = (
    PERFIL_2013_2018,
    PERFIL_2019,
    PERFIL_2020,
    PERFIL_2021,
    PERFIL_2022_2023,
    PERFIL_2024,
)

_MESES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}

_PATRON_PRECIO_MILES = re.compile(r"^(?:\d{1,3}(?:\.\d{3})*|\d+)$")


def _limpiar_texto(
    valor: str | None,
    *,
    campo: str,
    numero_fila: int,
) -> str:
    """Valida y elimina espacios periféricos de un campo obligatorio."""
    if valor is None:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Campo {campo!r} ausente en fila {numero_fila}."
        )

    texto = valor.strip()

    if not texto:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Campo {campo!r} vacío en fila {numero_fila}."
        )

    return texto


def _columnas_significativas(
    encabezado: Sequence[str],
) -> tuple[str, ...]:
    """Elimina columnas residuales completamente anónimas del encabezado."""
    return tuple(campo.strip() for campo in encabezado if campo.strip())


def _encabezado_coincide(
    encabezado: Sequence[str],
    perfil: PerfilEsquemaPrecioMensualSipsa,
) -> bool:
    """Determina si un encabezado pertenece a un perfil conocido."""
    if perfil.permite_columnas_vacias_extra:
        return _columnas_significativas(encabezado) == perfil.columnas

    return tuple(encabezado) == perfil.columnas


def detectar_perfil_precios_mensuales_sipsa(
    contenido_csv: bytes,
) -> PerfilEsquemaPrecioMensualSipsa:
    """Detecta de forma determinista la versión del esquema SIPSA_P."""
    if not contenido_csv:
        raise ErrorParserPreciosMensualesHistoricoSipsa("El contenido CSV está vacío.")

    for perfil in PERFILES_CONOCIDOS:
        try:
            texto = contenido_csv.decode(perfil.codificacion)
        except UnicodeDecodeError:
            continue

        lector = csv.reader(
            io.StringIO(texto, newline=""),
            delimiter=";",
        )

        encabezado = next(
            lector,
            None,
        )

        if encabezado is None:
            continue

        if _encabezado_coincide(
            encabezado,
            perfil,
        ):
            return perfil

    raise ErrorParserPreciosMensualesHistoricoSipsa(
        "El CSV SIPSA_P no corresponde a ninguno de los perfiles históricos conocidos."
    )


def _parsear_fecha_legada(
    valor: str,
    *,
    numero_fila: int,
) -> date:
    """Interpreta fechas del tipo d/mm/YYYY y normaliza al inicio del mes."""
    try:
        fecha = datetime.strptime(
            valor,
            "%d/%m/%Y",
        ).date()
    except ValueError as exc:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Fecha inválida en fila {numero_fila}: {valor!r}"
        ) from exc

    return fecha.replace(day=1)


def _parsear_fecha_abreviada(
    valor: str,
    *,
    numero_fila: int,
) -> date:
    """Interpreta fechas mensuales abreviadas como ene-22."""
    partes = valor.lower().split("-")

    if len(partes) != 2:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Fecha inválida en fila {numero_fila}: {valor!r}"
        )

    mes_texto, anio_texto = partes
    mes = _MESES.get(mes_texto)

    if mes is None:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Mes inválido en fila {numero_fila}: {valor!r}"
        )

    if len(anio_texto) != 2 or not anio_texto.isdigit():
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Año inválido en fila {numero_fila}: {valor!r}"
        )

    return date(
        2000 + int(anio_texto),
        mes,
        1,
    )


def _parsear_fecha(
    valor: str,
    *,
    perfil: PerfilEsquemaPrecioMensualSipsa,
    numero_fila: int,
) -> date:
    """Interpreta una fecha según el perfil de esquema."""
    if perfil.fecha_abreviada:
        return _parsear_fecha_abreviada(
            valor,
            numero_fila=numero_fila,
        )

    return _parsear_fecha_legada(
        valor,
        numero_fila=numero_fila,
    )


def _parsear_precio_entero(
    valor: str,
    *,
    numero_fila: int,
) -> Decimal:
    """Interpreta precios históricos publicados como enteros."""
    try:
        precio = Decimal(valor)
    except InvalidOperation as exc:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Precio inválido en fila {numero_fila}: {valor!r}"
        ) from exc

    if precio <= 0:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Precio no positivo en fila {numero_fila}: {valor!r}"
        )

    return precio


def _parsear_precio_miles(
    valor: str,
    *,
    numero_fila: int,
) -> Decimal:
    """Interpreta precios con punto como separador de miles."""
    if _PATRON_PRECIO_MILES.fullmatch(valor) is None:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Formato de precio inválido en fila {numero_fila}: {valor!r}"
        )

    precio = int(valor.replace(".", ""))

    if precio <= 0:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"Precio no positivo en fila {numero_fila}: {valor!r}"
        )

    return Decimal(precio)


def _parsear_precio(
    valor: str,
    *,
    perfil: PerfilEsquemaPrecioMensualSipsa,
    numero_fila: int,
) -> Decimal:
    """Interpreta el precio según el perfil histórico."""
    if perfil.precio_con_separador_miles:
        return _parsear_precio_miles(
            valor,
            numero_fila=numero_fila,
        )

    return _parsear_precio_entero(
        valor,
        numero_fila=numero_fila,
    )


def parsear_precios_mensuales_sipsa(
    contenido_csv: bytes,
    *,
    archivo_fuente: str,
) -> Iterator[ObservacionPrecioMensualSipsa]:
    """
    Normaliza cualquier esquema histórico SIPSA_P conocido.

    Todas las observaciones de la fuente se conservan. Si existen varias
    observaciones para la misma clave candidata, se emiten todas y la
    detección del conflicto corresponde a la capa de validación.
    """
    if not archivo_fuente.strip():
        raise ValueError("archivo_fuente no puede estar vacío.")

    perfil = detectar_perfil_precios_mensuales_sipsa(contenido_csv)

    try:
        texto = contenido_csv.decode(perfil.codificacion)
    except UnicodeDecodeError as exc:
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            f"No fue posible decodificar {archivo_fuente!r} con {perfil.codificacion!r}."
        ) from exc

    lector = csv.DictReader(
        io.StringIO(texto, newline=""),
        delimiter=";",
    )

    if lector.fieldnames is None:
        raise ErrorParserPreciosMensualesHistoricoSipsa("El CSV SIPSA_P no contiene encabezado.")

    if not _encabezado_coincide(
        lector.fieldnames,
        perfil,
    ):
        raise ErrorParserPreciosMensualesHistoricoSipsa(
            "El encabezado cambió durante la interpretación del CSV."
        )

    for numero_fila, registro in enumerate(
        lector,
        start=2,
    ):
        fecha_texto = _limpiar_texto(
            registro.get("Fecha"),
            campo="Fecha",
            numero_fila=numero_fila,
        )
        grupo = _limpiar_texto(
            registro.get("Grupo"),
            campo="Grupo",
            numero_fila=numero_fila,
        )
        producto = _limpiar_texto(
            registro.get("Producto"),
            campo="Producto",
            numero_fila=numero_fila,
        )
        mercado = _limpiar_texto(
            registro.get(perfil.campo_mercado),
            campo=perfil.campo_mercado,
            numero_fila=numero_fila,
        )
        precio_texto = _limpiar_texto(
            registro.get(perfil.campo_precio),
            campo=perfil.campo_precio,
            numero_fila=numero_fila,
        )

        codigo_cpc: str | None = None

        if perfil.campo_cpc is not None:
            codigo_cpc = _limpiar_texto(
                registro.get(perfil.campo_cpc),
                campo=perfil.campo_cpc,
                numero_fila=numero_fila,
            )

        yield ObservacionPrecioMensualSipsa(
            fecha_mes=_parsear_fecha(
                fecha_texto,
                perfil=perfil,
                numero_fila=numero_fila,
            ),
            producto=producto,
            mercado=mercado,
            grupo=grupo,
            codigo_cpc=codigo_cpc,
            precio_promedio_kg=_parsear_precio(
                precio_texto,
                perfil=perfil,
                numero_fila=numero_fila,
            ),
            fuente="SIPSA-DANE",
            archivo_fuente=archivo_fuente,
        )
