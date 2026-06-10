# src/controller/controlador_lineal.py
"""
controlador_lineal.py
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
from src.models.metodos.programacion_lineal_basica.resolucion_rapida import ResolutorGeneral
from src.models.metodos.programacion_lineal_basica.simplex import SolucionadorSimplex
from src.models.metodos.programacion_lineal_basica.m_grande import SolucionadorGranM
from src.models.metodos.programacion_lineal_basica.dos_fases import SolucionadorDosFases
from src.models.metodos.programacion_lineal_basica.historial_de_problemas import HistorialDeProblemas

# Importaciones estrictas de las entidades inmutables del dominio de objetos
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal.respuesta import RespuestaSciPyPL, RespuestaTabularPL


class ControladorLineal:
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
        """Inicializa el controlador general del sistema y la referencia de estado."""
        self._problema_activo: Optional[ProblemaPL] = None

    @property
    def problema_activo(self) -> Optional[ProblemaPL]:
        """Retorna la entidad del problema matemático activo en la sesión actual."""
        return self._problema_activo

    @problema_activo.setter
    def problema_activo(self, problema: Optional[ProblemaPL]) -> None:
        """Asigna de manera explícita y controlada la entidad del problema activo."""
        self._problema_activo = problema

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
        Persiste un modelo de programación lineal en el histórico del sistema 
        y lo establece automáticamente como el problema activo de la sesión.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad del dominio inmutable.
        """
        problema_guardado = self._historial_de_problema.ingresar_problema(problema)
        self._problema_activo = problema_guardado  # Asignación automática al ingresar nuevo
        return problema_guardado

    def obtener_problema_por_indice(self, indice: int) -> ProblemaPL:
        """
        Recupera un modelo lineal del histórico basándose en su posición y lo
        establece automáticamente como el problema activo de la sesión.

        Parámetros
        ----------
        indice : int
            Posición de la entidad en la lista de almacenamiento.
        """
        problema_seleccionado = self._historial_de_problema.obtener_problemas(indice)
        self._problema_activo = problema_seleccionado  # Asignación automática al seleccionar del historial
        return problema_seleccionado

    def eliminar_problema_por_indice(self, indice: int) -> ProblemaPL:
        """
        Remueve una entidad del histórico y limpia de forma segura la referencia activa 
        en caso de que el problema eliminado sea el que se encontraba seleccionado.

        Parámetros
        ----------
        indice : int
            Posición del elemento que se va a purgar de la memoria.
        """
        # Recuperar el objeto antes de eliminarlo para validar la referencia actual
        problema_a_eliminar = self._historial_de_problema.obtener_problemas(indice)
        
        # Si el problema que se elimina coincide con el activo, limpiamos la pantalla activa
        if self._problema_activo == problema_a_eliminar:
            self._problema_activo = None

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