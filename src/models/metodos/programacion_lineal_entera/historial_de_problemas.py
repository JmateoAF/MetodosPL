# src/models/metodos/programacion_lineal_entera/historial_de_problemas.py
"""
historial_de_problemas.py
=========================
Módulo encargado de la persistencia en memoria y gestión del histórico 
de modelos de Programación Lineal Entera utilizando objetos de dominio.
"""

from typing import List, Union
from src.models.entity.programacion_lineal_entera.problema import ProblemaPLE, ProblemaModeladoLogico


class HistorialDeProblemasEntera:
    """
    Gestiona el almacenamiento y operaciones sobre el historial de problemas 
    de programación lineal entera, garantizando el uso exclusivo de entidades POO puras.
    """

    def __init__(self) -> None:
        """Inicializa el contenedor del histórico como una lista fuertemente tipada."""
        self._historial_de_problemas: List[Union[ProblemaPLE, ProblemaModeladoLogico]] = []

    def ingresar_problema(self, problema: Union[ProblemaPLE, ProblemaModeladoLogico]) -> Union[ProblemaPLE, ProblemaModeladoLogico]:
        """
        Guarda un modelo de programación lineal entera en el historial.
        """
        self._historial_de_problemas.append(problema)
        return problema

    def obtener_historial_de_problemas(self) -> List[Union[ProblemaPLE, ProblemaModeladoLogico]]:
        """
        Devuelve la lista completa de problemas almacenados en el histórico.
        """
        return self._historial_de_problemas

    def obtener_problemas(self, indice: int) -> Union[ProblemaPLE, ProblemaModeladoLogico]:
        """
        Recupera un problema específico a partir de su índice posicional.
        """
        return self._historial_de_problemas[indice]

    def eliminar_problema(self, indice: int) -> Union[ProblemaPLE, ProblemaModeladoLogico]:
        """
        Elimina y devuelve un problema del histórico basándose en su índice.
        """
        return self._historial_de_problemas.pop(indice)
    
    def es_indice_valido(self, indice: int) -> bool:
        """
        Verifica si un índice posicional existe dentro del rango actual del historial.
        """
        return 0 <= indice < len(self._historial_de_problemas)
