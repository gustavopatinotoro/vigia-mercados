"""
Pruebas del fallback territorial geoespacial MGN.
"""

from decimal import Decimal

import pytest

from vigia.dominio.clima import EstacionIdeam
from vigia.dominio.territorio import (
    EntidadTerritorialCanonica,
    TipoEntidadTerritorial,
)
from vigia.infraestructura.territorio import (
    ErrorResolucionTerritorial,
    MunicipioMgn,
    ResolvedorTerritorial,
    ResolvedorTerritorialGeoespacial,
)


class ClienteMgnFalso:
    """Cliente MGN controlado para pruebas."""

    def __init__(
        self,
        resultado: MunicipioMgn | None,
    ) -> None:
        self.resultado = resultado
        self.consultas = 0

    def resolver_punto(
        self,
        *,
        latitud: Decimal,
        longitud: Decimal,
        timeout_segundos: float = 30.0,
    ) -> MunicipioMgn | None:
        self.consultas += 1

        assert Decimal("-90") <= latitud <= Decimal("90")
        assert Decimal("-180") <= longitud <= Decimal("180")
        assert timeout_segundos > 0

        return self.resultado


def _entidad(
    *,
    codigo: str,
    departamento: str,
    nombre: str,
) -> EntidadTerritorialCanonica:
    return EntidadTerritorialCanonica(
        codigo_divipola=codigo,
        codigo_departamento=codigo[:2],
        departamento=departamento,
        nombre=nombre,
        tipo=TipoEntidadTerritorial.MUNICIPIO,
        latitud=Decimal("6.5"),
        longitud=Decimal("-75.5"),
    )


def _estacion(
    *,
    departamento: str,
    municipio: str,
) -> EstacionIdeam:
    return EstacionIdeam(
        codigo="001",
        nombre="ESTACION DE PRUEBA",
        categoria="Climatológica",
        tecnologia="Automática",
        estado="Activa",
        departamento=departamento,
        municipio=municipio,
        latitud=Decimal("6.48"),
        longitud=Decimal("-75.63"),
        altitud_m=Decimal("2400"),
        entidad="IDEAM",
    )


def _resolvedor_base() -> ResolvedorTerritorial:
    return ResolvedorTerritorial(
        [
            _entidad(
                codigo="05664",
                departamento="ANTIOQUIA",
                nombre="SAN PEDRO DE LOS MILAGROS",
            ),
            _entidad(
                codigo="05237",
                departamento="ANTIOQUIA",
                nombre="DONMATÍAS",
            ),
        ]
    )


def test_no_consulta_mgn_si_resuelve_nominalmente() -> None:
    cliente = ClienteMgnFalso(
        MunicipioMgn(
            codigo_divipola="05237",
            departamento="ANTIOQUIA",
            municipio="DONMATÍAS",
        )
    )

    resolvedor = ResolvedorTerritorialGeoespacial(
        resolvedor_base=_resolvedor_base(),
        cliente_mgn=cliente,
    )

    resultado = resolvedor.resolver_estacion_ideam(
        _estacion(
            departamento="Antioquia",
            municipio="San Pedro De Los Milagros",
        )
    )

    assert resultado.territorio.codigo_divipola == "05664"
    assert cliente.consultas == 0


def test_resuelve_por_mgn_si_falla_resolucion_nominal() -> None:
    cliente = ClienteMgnFalso(
        MunicipioMgn(
            codigo_divipola="05664",
            departamento="ANTIOQUIA",
            municipio="SAN PEDRO DE LOS MILAGROS",
        )
    )

    resolvedor = ResolvedorTerritorialGeoespacial(
        resolvedor_base=_resolvedor_base(),
        cliente_mgn=cliente,
    )

    resultado = resolvedor.resolver_estacion_ideam(
        _estacion(
            departamento="Antioquia",
            municipio="San Pedro",
        )
    )

    assert resultado.territorio.codigo_divipola == "05664"
    assert cliente.consultas == 1


def test_rechaza_punto_sin_interseccion_mgn() -> None:
    cliente = ClienteMgnFalso(None)

    resolvedor = ResolvedorTerritorialGeoespacial(
        resolvedor_base=_resolvedor_base(),
        cliente_mgn=cliente,
    )

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="nombre, alias ni intersección geoespacial MGN",
    ):
        resolvedor.resolver_estacion_ideam(
            _estacion(
                departamento="Antioquia",
                municipio="Territorio inexistente",
            )
        )

    assert cliente.consultas == 1


def test_rechaza_codigo_mgn_ausente_del_catalogo_canonico() -> None:
    cliente = ClienteMgnFalso(
        MunicipioMgn(
            codigo_divipola="05999",
            departamento="ANTIOQUIA",
            municipio="MUNICIPIO DESCONOCIDO",
        )
    )

    resolvedor = ResolvedorTerritorialGeoespacial(
        resolvedor_base=_resolvedor_base(),
        cliente_mgn=cliente,
    )

    with pytest.raises(
        ErrorResolucionTerritorial,
        match="Código DIVIPOLA desconocido",
    ):
        resolvedor.resolver_estacion_ideam(
            _estacion(
                departamento="Antioquia",
                municipio="Territorio inexistente",
            )
        )
