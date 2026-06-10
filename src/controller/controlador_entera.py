# src/controller/controlador_entera.py
"""
controlador_entera.py
=====================
Controlador especializado para los algoritmos de Programación Lineal Entera (PI).
(En fase de diseño arquitectónico).
"""

from typing import Optional

class ControladorEntera:
    def __init__(self) -> None:
        self._problema_activo = None

    @property
    def problema_activo(self):
        return self._problema_activo

    @problema_activo.setter
    def problema_activo(self, problema) -> None:
        self._problema_activo = problema