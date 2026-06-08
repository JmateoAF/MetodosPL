# src/controller/controlador.py
"""
controlador.py
==============
Capa del Controlador Central en la arquitectura MVC del optimizador lineal.

Responsabilidades:
    - Actuar como el mediador unificado entre las vistas de la interfaz (UI) y la capa de modelos.
    - Orquestar las llamadas a los solucionadores matemáticos puros e inmutables.
    - Gestionar el ciclo de vida del histórico de problemas en memoria sin fugas de tipado.

Autor: Central Controller Module — MVC Linear Optimizer
"""

from typing import List, Optional, Union

# Importaciones de Solvers corregidas de acuerdo a la nueva jerarquía modular de la arquitectura POO
from src.models.metodos.resolucion_rapida import ResolutorGeneral
from src.models.metodos.simplex import SolucionadorSimplex
from src.models.metodos.m_grande import SolucionadorGranM
from src.models.metodos.dos_fases import SolucionadorDosFases
from src.models.metodos.historial_de_problemas import HistorialDeProblemas

# Importaciones estrictas de las entidades inmutables del dominio de objetos
from src.models.entity.problema import ProblemaPL
from src.models.entity.respuesta import RespuestaSciPyPL, RespuestaTabularPL


class Controlador:
    """
    Orquestador central y único punto de contacto para la ejecución de algoritmos 
    y persistencia de datos del dominio, operando de forma exclusiva bajo POO.
    """

    # Compartición estática intencional a nivel de clase para actuar como instancias unificadas (Singletons de facto)
    _solver_casos_general: ResolutorGeneral = ResolutorGeneral()
    _solver_simplex: SolucionadorSimplex = SolucionadorSimplex()
    _solver_M_grande: SolucionadorGranM = SolucionadorGranM()
    _solver_dos_fases: SolucionadorDosFases = SolucionadorDosFases()
    _historial_de_problema: HistorialDeProblemas = HistorialDeProblemas()

    def __init__(self) -> None:
        """Inicializa el controlador general del sistema."""
        pass

    def resolver_LP(self, problema: ProblemaPL, opcion: int) -> Optional[Union[RespuestaSciPyPL, RespuestaTabularPL]]:
        """
        Deriva el modelo lineal inmutable hacia el solucionador matemático seleccionado.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad inmutable que representa el modelo matemático formal a resolver.
        opcion : int
            Identificador numérico estricto del método de resolución deseado:
            1 -> Método General Analítico (Basado en SciPy con precisión flotante).
            2 -> Método Simplex Tabular Clásico (Aritmética exacta con fracciones).
            3 -> Método de la M Grande (Penalización exacta Big-M).
            4 -> Método de las Dos Fases (Suma y remoción de variables artificiales).

        Retorna
        -------
        Optional[Union[RespuestaSciPyPL, RespuestaTabularPL]]
            Instancia inmutable que contiene la solución matemática detallada, 
            o None en caso de ingresar una opción inválida.
        """
        match opcion:
            case 1:
                return self._solver_casos_general.resolver(problema)
            case 2:
                return self._solver_simplex.resolver(problema)
            case 3:
                return self._solver_M_grande.resolver(problema)
            case 4:
                return self._solver_dos_fases.resolver(problema)
            case _:
                return None

    def ingresar_problema(self, problema: ProblemaPL) -> ProblemaPL:
        """
        Persiste un modelo de programación lineal en el histórico del sistema.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad del dominio inmutable.
        """
        return self._historial_de_problema.ingresar_problema(problema)

    def obtener_problema_por_indice(self, indice: int) -> ProblemaPL:
        """
        Recupera un modelo lineal del histórico basándose en su posición.

        Parámetros
        ----------
        indice : int
            Posición de la entidad en la lista de almacenamiento.
        """
        return self._historial_de_problema.obtener_problemas(indice)

    def eliminar_problema_por_indice(self, indice: int) -> ProblemaPL:
        """
        Remueve una entidad del histórico y devuelve el objeto eliminado.

        Parámetros
        ----------
        indice : int
            Posición del elemento que se va a purgar de la memoria.
        """
        return self._historial_de_problema.eliminar_problema(indice)

    def obtener_historial_completo(self) -> List[ProblemaPL]:
        """
        Devuelve el histórico íntegro y tipado de los modelos almacenados.

        Retorna
        -------
        List[ProblemaPL]
            Colección de objetos inmutables del dominio.
        """
        return self._historial_de_problema.obtener_historial_de_problemas()
    