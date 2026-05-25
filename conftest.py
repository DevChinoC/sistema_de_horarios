"""
conftest.py — Configuración global de pytest.

Agrega el directorio raíz del proyecto al sys.path para que
todos los módulos (domain, application, infrastructure, ui) sean
importables desde los tests sin necesidad de instalar el paquete.
"""
import sys
import os

# Raíz del proyecto (donde vive este conftest.py)
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
