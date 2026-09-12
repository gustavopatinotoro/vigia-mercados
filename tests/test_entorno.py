"""
Pruebas fundamentales del entorno de VIGÍA.

Estas pruebas verifican que el paquete pueda importarse correctamente
y que la versión mínima del intérprete sea respetada.
"""

import sys

import vigia


def test_version_python() -> None:
    """Verifica que VIGÍA se ejecute sobre Python 3.14 o superior."""
    assert sys.version_info >= (3, 14)


def test_version_paquete() -> None:
    """Verifica que el paquete exponga una versión válida."""
    assert vigia.__version__ == "0.1.0"
