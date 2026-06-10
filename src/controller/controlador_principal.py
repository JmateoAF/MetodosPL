"""
controlador_principal.py
========================
Implementa el Patrón Fachada (Facade) para orquestar los distintos
sub-controladores matemáticos del ecosistema.
"""

from src.controller.controlador_lineal import ControladorLineal
from src.controller.controlador_entera import ControladorEntera

class ControladorPrincipal:
    """
    Punto de entrada único para la gestión del dominio.
    Instancia y expone los sub-controladores especializados.
    """
    def __init__(self) -> None:
        self.lineal: ControladorLineal = ControladorLineal()
        self.entera: ControladorEntera = ControladorEntera()