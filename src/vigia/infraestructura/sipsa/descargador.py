"""
Descarga reproducible de archivos oficiales SIPSA.

La descarga se realiza por bloques directamente a disco para evitar mantener
archivos grandes completos en memoria. Cada archivo queda acompañado de
información suficiente para verificar su procedencia e integridad.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ErrorDescargaSipsa(RuntimeError):
    """Error durante la adquisición de una fuente oficial SIPSA."""


@dataclass(frozen=True, slots=True)
class ResultadoDescargaSipsa:
    """Resultado verificable de una descarga SIPSA."""

    ruta: Path
    url: str
    tamanio_bytes: int
    sha256: str
    tipo_contenido: str


TAMANIO_BLOQUE = 1024 * 1024
AGENTE_USUARIO = "VIGIA-Mercados/0.1"

TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def descargar_xlsx_sipsa(
    url: str,
    *,
    destino: Path,
    timeout_segundos: float = 120.0,
) -> ResultadoDescargaSipsa:
    """
    Descarga un XLSX SIPSA directamente a disco.

    La operación:
    - no acumula el archivo completo en RAM;
    - calcula SHA-256 mientras recibe los datos;
    - valida HTTP, tipo MIME y firma ZIP/XLSX;
    - elimina archivos parciales cuando ocurre un error.
    """
    destino.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporal = destino.with_suffix(f"{destino.suffix}.parcial")

    solicitud = Request(
        url,
        headers={
            "User-Agent": AGENTE_USUARIO,
            "Accept": TIPO_XLSX,
        },
    )

    resumen = sha256()
    tamanio = 0
    primeros_bytes = b""

    try:
        with urlopen(
            solicitud,
            timeout=timeout_segundos,
        ) as respuesta:
            if respuesta.status != 200:
                raise ErrorDescargaSipsa(f"HTTP inesperado: {respuesta.status}")

            tipo_contenido = (
                (respuesta.headers.get("Content-Type") or "").split(";", maxsplit=1)[0].strip()
            )

            if tipo_contenido != TIPO_XLSX:
                raise ErrorDescargaSipsa(f"Tipo de contenido inesperado: {tipo_contenido!r}")

            with temporal.open("wb") as archivo:
                while bloque := respuesta.read(TAMANIO_BLOQUE):
                    if not primeros_bytes:
                        primeros_bytes = bloque[:4]

                    archivo.write(bloque)
                    resumen.update(bloque)
                    tamanio += len(bloque)

    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        temporal.unlink(missing_ok=True)
        raise ErrorDescargaSipsa(f"No fue posible descargar SIPSA desde {url!r}: {exc}") from exc

    except ErrorDescargaSipsa:
        temporal.unlink(missing_ok=True)
        raise

    if primeros_bytes != b"PK\x03\x04":
        temporal.unlink(missing_ok=True)
        raise ErrorDescargaSipsa("El contenido descargado no tiene una firma XLSX válida.")

    if tamanio == 0:
        temporal.unlink(missing_ok=True)
        raise ErrorDescargaSipsa("El archivo descargado está vacío.")

    temporal.replace(destino)

    return ResultadoDescargaSipsa(
        ruta=destino,
        url=url,
        tamanio_bytes=tamanio,
        sha256=resumen.hexdigest(),
        tipo_contenido=tipo_contenido,
    )
