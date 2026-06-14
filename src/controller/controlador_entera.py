# src/controller/controlador_entera.py
"""
controlador_entera.py
=====================
Controlador especializado para los algoritmos de Programación Lineal Entera (PLE),
Mixta (MILP) y lógica booleana avanzada.
"""

from typing import List, Optional, Union

# Importaciones de solvers y compilador
from src.models.metodos.programacion_lineal_entera.branch_and_bound import SolucionadorBranchAndBound
from src.models.metodos.programacion_lineal_entera.planos_corte import SolucionadorPlanosCorte
from src.models.metodos.programacion_lineal_entera.enumeracion_implicita import SolucionadorEnumeracionImplicita
from src.models.metodos.programacion_lineal_entera.historial_de_problemas import HistorialDeProblemasEntera
from src.utils.programacion_lineal_entera.compilador_logica import CompiladorLogico

# Importaciones de entidades
from src.models.entity.programacion_lineal_entera.problema import ProblemaPLE, ProblemaModeladoLogico
from src.models.entity.programacion_lineal_entera.respuesta import (
    RespuestaBranchAndBound,
    RespuestaPlanoCorte,
    RespuestaEnumeracionImplicita,
)


class ControladorEntera:
    """
    Orquestador central y único punto de contacto para la ejecución de algoritmos 
    y persistencia de datos de programación lineal entera.
    """

    _solver_branch_and_bound: SolucionadorBranchAndBound = SolucionadorBranchAndBound()
    _solver_planos_corte: SolucionadorPlanosCorte = SolucionadorPlanosCorte()
    _solver_enumeracion_implicita: SolucionadorEnumeracionImplicita = SolucionadorEnumeracionImplicita()
    _historial_de_problema: HistorialDeProblemasEntera = HistorialDeProblemasEntera()
    _compilador_logico: CompiladorLogico = CompiladorLogico()

    def __init__(self) -> None:
        """Inicializa el controlador y el problema activo."""
        self._problema_activo: Optional[Union[ProblemaPLE, ProblemaModeladoLogico]] = None

    @property
    def problema_activo(self) -> Optional[Union[ProblemaPLE, ProblemaModeladoLogico]]:
        """Retorna la entidad del problema matemático activo en la sesión actual."""
        return self._problema_activo

    @problema_activo.setter
    def problema_activo(self, problema: Optional[Union[ProblemaPLE, ProblemaModeladoLogico]]) -> None:
        """Asigna el problema activo."""
        self._problema_activo = problema

    def resolver_PLE(
        self,
        problema: Union[ProblemaPLE, ProblemaModeladoLogico],
        opcion: int,
        metodo_lineal: Optional[int] = None,
    ) -> Optional[Union[RespuestaBranchAndBound, RespuestaPlanoCorte, RespuestaEnumeracionImplicita]]:
        """
        Deriva el modelo entero inmutable al solucionador matemático seleccionado,
        compilando previamente si se trata de un modelo lógico.

        Parámetros
        ----------
        problema : Union[ProblemaPLE, ProblemaModeladoLogico]
            Entidad inmutable del problema.
        opcion : int
            1 -> Branch and Bound (Mixto/Entero)
            2 -> Planos de Corte (Cortes de Gomory)
            3 -> Enumeración Implícita (Balas para variables binarias)
        metodo_lineal : Optional[int]
            Método continuo subyacente a utilizar (ver SolucionadorBranchAndBound).

        Retorna
        -------
        Respuesta del solucionador seleccionado.
        """
        # Si es un modelo lógico, compilarlo primero a un ProblemaPLE plano
        problema_ple: ProblemaPLE
        if isinstance(problema, ProblemaModeladoLogico):
            problema_ple = self._compilador_logico.compilar(problema)
        else:
            problema_ple = problema

        match opcion:
            case 1:
                # Si el usuario seleccionó un método lineal específico para B&B, creamos una nueva instancia temporal
                if metodo_lineal is not None:
                    solver = SolucionadorBranchAndBound(metodo_lineal=metodo_lineal)
                    return solver.resolver(problema_ple)
                return self._solver_branch_and_bound.resolver(problema_ple)
            case 2:
                return self._solver_planos_corte.resolver(problema_ple)
            case 3:
                return self._solver_enumeracion_implicita.resolver(problema_ple)
            case _:
                return None

    def ingresar_problema(self, problema: Union[ProblemaPLE, ProblemaModeladoLogico]) -> Union[ProblemaPLE, ProblemaModeladoLogico]:
        """
        Persiste un modelo en el histórico de programación entera y lo establece como activo.
        """
        problema_guardado = self._historial_de_problema.ingresar_problema(problema)
        self._problema_activo = problema_guardado
        return problema_guardado

    def obtener_problema_por_indice(self, indice: int) -> Union[ProblemaPLE, ProblemaModeladoLogico]:
        """
        Recupera un modelo del histórico y lo establece como activo.
        """
        problema_seleccionado = self._historial_de_problema.obtener_problemas(indice)
        self._problema_activo = problema_seleccionado
        return problema_seleccionado

    def eliminar_problema_por_indice(self, indice: int) -> Union[ProblemaPLE, ProblemaModeladoLogico]:
        """
        Elimina un problema del histórico.
        """
        problema_a_eliminar = self._historial_de_problema.obtener_problemas(indice)
        if self._problema_activo == problema_a_eliminar:
            self._problema_activo = None
        return self._historial_de_problema.eliminar_problema(indice)

    def obtener_historial_completo(self) -> List[Union[ProblemaPLE, ProblemaModeladoLogico]]:
        """
        Devuelve el histórico íntegro de los modelos de programación entera.
        """
        return self._historial_de_problema.obtener_historial_de_problemas()