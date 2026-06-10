# src/models/metodos/historial_de_problemas.py
"""
historial_de_problemas.py
=========================
Módulo encargado de la persistencia en memoria y gestión del histórico 
de modelos de Programación Lineal utilizando objetos de dominio.

Responsabilidades:
    - Almacenar, recuperar y eliminar instancias inmutables de ProblemaPL.
    - Garantizar que no existan mutaciones colaterales en el histórico.

Autor: Backend Module — MVC Linear Optimizer
"""

from typing import List
from src.models.entity.programacion_lineal.problema import ProblemaPL


class HistorialDeProblemas:
    """
    Gestiona el almacenamiento y operaciones sobre el historial de problemas 
    de programación lineal, garantizando el uso exclusivo de entidades POO puras.
    """

    def __init__(self) -> None:
        """Inicializa el contenedor del histórico como una lista fuertemente tipada."""
        self._historial_de_problemas: List[ProblemaPL] = []

    def ingresar_problema(self, problema: ProblemaPL) -> ProblemaPL:
        """
        Guarda un modelo de programación lineal en el historial.

        Parámetros
        ----------
        problema : ProblemaPL
            Instancia inmutable del problema a persistir.

        Retorna
        -------
        ProblemaPL
            La misma instancia guardada para dar continuidad al flujo funcional.
        """
        self._historial_de_problemas.append(problema)
        return problema

    def obtener_historial_de_problemas(self) -> List[ProblemaPL]:
        """
        Devuelve la lista completa de problemas almacenados en el histórico.

        Retorna
        -------
        List[ProblemaPL]
            Lista con todas las entidades inmutables guardadas.
        """
        return self._historial_de_problemas

    def obtener_problemas(self, indice: int) -> ProblemaPL:
        """
        Recupera un problema específico a partir de su índice posicional.

        Parámetros
        ----------
        indice : int
            Posición del problema dentro del histórico.

        Retorna
        -------
        ProblemaPL
            La entidad inmutable del problema solicitado.
        """
        return self._historial_de_problemas[indice]

    def eliminar_problema(self, indice: int) -> ProblemaPL:
        """
        Elimina y devuelve un problema del histórico basándose en su índice.

        Parámetros
        ----------
        indice : int
            Posición del elemento que se desea remover.

        Retorna
        -------
        ProblemaPL
            La entidad del problema que acaba de ser removida.
        """
        return self._historial_de_problemas.pop(indice)
    
    def es_indice_valido(self, indice: int) -> bool:
        """
        Verifica si un índice posicional existe dentro del rango actual del historial.

        Parámetros
        ----------
        indice : int
            Posición del elemento que se desea verificar si existe

        Retorna
        -------
        boool
            un booleano indicando si ese indice es valido o no
        """
        return 0 <= indice < len(self._historial_de_problemas)