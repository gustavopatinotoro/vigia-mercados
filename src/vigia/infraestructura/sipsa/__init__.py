"""
Infraestructura de integración con SIPSA.

Expone la interfaz pública de los adaptadores utilizados para adquirir,
interpretar y canonizar las fuentes externas publicadas por el DANE.
"""

from vigia.infraestructura.sipsa.canonizacion_operacional import (
    ErrorCanonizacionOperacionalSipsa,
    mercados_sipsa_p_soportados,
    normalizar_producto_sipsa,
    resolver_mercado_sipsa_p,
)
from vigia.infraestructura.sipsa.correspondencias_productos import (
    CORRESPONDENCIAS_PRODUCTOS_SIPSA,
    CorrespondenciaProductoSipsa,
    TipoCorrespondenciaProducto,
    obtener_correspondencia_producto,
    productos_abastecimiento_equivalentes,
)
from vigia.infraestructura.sipsa.descargador import (
    ErrorDescargaSipsa,
    ResultadoDescargaSipsa,
    descargar_xlsx_sipsa,
)
from vigia.infraestructura.sipsa.parser_abastecimiento import (
    ErrorParserAbastecimientoSipsa,
    parsear_abastecimiento_sipsa,
)
from vigia.infraestructura.sipsa.parser_precios import (
    ErrorParserPreciosSipsa,
    parsear_precios_sipsa,
)
from vigia.infraestructura.sipsa.parser_precios_mensuales_historico import (
    ErrorParserPreciosMensualesHistoricoSipsa,
    PerfilEsquemaPrecioMensualSipsa,
    detectar_perfil_precios_mensuales_sipsa,
    parsear_precios_mensuales_sipsa,
)
from vigia.infraestructura.sipsa.parser_precios_mensuales_legado import (
    ErrorParserPreciosMensualesLegadoSipsa,
    leer_csv_desde_zip_sipsa,
    parsear_precios_mensuales_legado_sipsa,
)
from vigia.infraestructura.sipsa.parser_precios_mensuales_moderno import (
    ErrorParserPreciosMensualesModernoSipsa,
    leer_csv_desde_zip_sipsa_moderno,
    parsear_precios_mensuales_moderno_sipsa,
)

__all__ = [
    "CORRESPONDENCIAS_PRODUCTOS_SIPSA",
    "CorrespondenciaProductoSipsa",
    "ErrorCanonizacionOperacionalSipsa",
    "ErrorDescargaSipsa",
    "ErrorParserAbastecimientoSipsa",
    "ErrorParserPreciosMensualesHistoricoSipsa",
    "ErrorParserPreciosMensualesLegadoSipsa",
    "ErrorParserPreciosMensualesModernoSipsa",
    "ErrorParserPreciosSipsa",
    "PerfilEsquemaPrecioMensualSipsa",
    "ResultadoDescargaSipsa",
    "TipoCorrespondenciaProducto",
    "descargar_xlsx_sipsa",
    "detectar_perfil_precios_mensuales_sipsa",
    "leer_csv_desde_zip_sipsa",
    "leer_csv_desde_zip_sipsa_moderno",
    "mercados_sipsa_p_soportados",
    "normalizar_producto_sipsa",
    "obtener_correspondencia_producto",
    "parsear_abastecimiento_sipsa",
    "parsear_precios_mensuales_legado_sipsa",
    "parsear_precios_mensuales_moderno_sipsa",
    "parsear_precios_mensuales_sipsa",
    "parsear_precios_sipsa",
    "productos_abastecimiento_equivalentes",
    "resolver_mercado_sipsa_p",
]
