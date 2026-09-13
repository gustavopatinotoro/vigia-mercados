"""
Canonización operacional conservadora entre fuentes SIPSA_P y SIPSA_A.

Este módulo resuelve únicamente diferencias editoriales demostradas entre
el boletín diario de precios y los microdatos de abastecimiento.

Principios:

- no utiliza fuzzy matching;
- no infiere equivalencias semánticas entre productos;
- elimina únicamente marcas editoriales conocidas y diferencias de espacios;
- los mercados se resuelven mediante correspondencias explícitas auditables.
"""

from __future__ import annotations


class ErrorCanonizacionOperacionalSipsa(RuntimeError):
    """Error al canonizar una entidad operacional SIPSA."""


_MERCADOS_SIPSA_P_A_SIPSA_A: dict[str, str] = {
    "CMA": "Medellín, Central Mayorista de Antioquia",
    "Cenabastos": "Cúcuta, Cenabastos",
    "Centroabastos": "Bucaramanga, Centroabastos",
    "Corabastos": "Bogotá, D.C., Corabastos",
    "La 21": "Ibagué, Plaza La 21",
    "La 41-Impala": "Pereira, La 41-Impala",
    "Mercar": "Armenia, Mercar",
    "Santa Elena": "Cali, Santa Elena",
    "Santa Marta": "Santa Marta (Magdalena)",
    "Surabastos": "Neiva, Surabastos",
    "Tunja": "Tunja, Complejo de Servicios del Sur",
}


def normalizar_producto_sipsa(
    producto: str,
) -> str:
    """
    Normaliza un producto sin alterar su significado comercial.

    Sólo se aplican transformaciones demostradas en SIPSA_P:

    - espacios periféricos;
    - asterisco editorial final;
    - múltiples espacios internos.

    No se singulariza, no se eliminan variedades y no se realizan
    correspondencias aproximadas.
    """
    texto = producto.strip()

    if texto.endswith("*"):
        texto = texto[:-1].strip()

    texto = " ".join(texto.split())

    if not texto:
        raise ValueError("El producto SIPSA no puede quedar vacío tras normalizarse.")

    return texto


def resolver_mercado_sipsa_p(
    mercado: str,
) -> str:
    """
    Resuelve un nombre de mercado de SIPSA_P a la identidad usada por SIPSA_A.

    La resolución es exclusivamente por catálogo explícito.
    """
    mercado_limpio = " ".join(mercado.strip().split())

    if not mercado_limpio:
        raise ValueError("El mercado SIPSA_P no puede estar vacío.")

    resultado = _MERCADOS_SIPSA_P_A_SIPSA_A.get(mercado_limpio)

    if resultado is None:
        raise ErrorCanonizacionOperacionalSipsa(
            f"No existe correspondencia explícita SIPSA_P -> SIPSA_A para el mercado {mercado!r}."
        )

    return resultado


def mercados_sipsa_p_soportados() -> tuple[str, ...]:
    """Devuelve los mercados SIPSA_P cubiertos por el catálogo explícito."""
    return tuple(sorted(_MERCADOS_SIPSA_P_A_SIPSA_A))
