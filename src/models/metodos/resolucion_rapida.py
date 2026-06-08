# src/models/metodos/resolucion_rapida.py
"""
resolucion_rapida.py
====================
Módulo de backend para la resolución eficiente de problemas de Programación
Lineal (PL) usando el "Método General" basado en scipy.optimize.linprog.

Responsabilidades:
    - Transformar la entidad inmutable ProblemaPL al formato exigido por linprog.
    - Retornar una entidad inmutable RespuestaSciPyPL con los datos íntegros.

Sin dependencias de diccionarios o interfaces dinámicas.
Autor: Backend Module — MVC Linear Optimizer
"""

import numpy as np
from scipy.optimize import linprog
from typing import List, Tuple, Optional

# Importaciones estrictas de las entidades de dominio orientadas a objetos
from src.models.entity.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.problema import ProblemaPL
from src.models.entity.respuesta import RespuestaSciPyPL


class ResolutorGeneral:
    """
    Encapsula la lógica de transformación y resolución de un problema de
    Programación Lineal mediante scipy.optimize.linprog utilizando objetos de dominio.
    """

    def __init__(self) -> None:
        """Inicializa las estructuras internas de cálculo del resolutor."""
        self._c: Optional[np.ndarray] = None        # Coeficientes objetivo ajustados para linprog
        self._A_ub: List[np.ndarray] = []           # Filas de restricciones de desigualdad (<=)
        self._b_ub: List[float] = []                # Valores del lado derecho (RHS) para desigualdad
        self._A_eq: List[np.ndarray] = []           # Filas de restricciones de igualdad (==)
        self._b_eq: List[float] = []                # Valores del lado derecho (RHS) para igualdad
        self._es_max: bool = False                  # Bandera de control para maximización

    def resolver(self, problema: ProblemaPL) -> RespuestaSciPyPL:
        """
        Ejecuta la resolución completa de un modelo de programación lineal.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad inmutable que contiene el modelo matemático formal.

        Retorna
        -------
        RespuestaSciPyPL
            Entidad inmutable con el resultado completo y los datos nativos de SciPy.
        """
        try:
            # --- 1. Preparación de datos mediante POO y métodos limpios ---
            self._preparar_objetivo(problema)
            self._preparar_restricciones(problema)
            
            A_ub, b_ub, A_eq, b_eq = self._construir_matrices()
            bounds = self._construir_bounds()

            # --- 2. Ejecución del motor matemático SciPy ---
            resultado_scipy = linprog(
                c=self._c,
                A_ub=A_ub,
                b_ub=b_ub,
                A_eq=A_eq,
                b_eq=b_eq,
                bounds=bounds,
                method="highs",  # Algoritmos de alto rendimiento lineales y enteros
            )

            # --- 3. Mapeo semántico estricto de códigos SciPy a un único Enum ---
            estado_unificado = self._mapear_codigo_scipy(resultado_scipy.status)
            mensaje_unificado = estado_unificado.value

            # --- 4. Postproceso de la solución y construcción de la entidad ---
            x_solucion: Optional[List[float]] = None
            fun_objetivo: Optional[float] = None
            slack_final: Optional[List[float]] = None
            con_final: Optional[List[float]] = None

            if resultado_scipy.status == 0:
                # Si el problema original era de maximización, revertimos el signo del óptimo hallado
                fun_objetivo = float(resultado_scipy.fun)
                if self._es_max:
                    fun_objetivo = -fun_objetivo

                x_solucion = [float(v) for v in resultado_scipy.x]
                slack_final = [float(s) for s in resultado_scipy.slack] if resultado_scipy.slack is not None else None
                con_final = [float(c) for c in resultado_scipy.con] if resultado_scipy.con is not None else None

            return RespuestaSciPyPL(
                estado=estado_unificado,
                mensaje=mensaje_unificado,
                x=x_solucion,
                fun=fun_objetivo,
                status=int(resultado_scipy.status),
                message=str(resultado_scipy.message),
                nit=int(resultado_scipy.nit),
                slack=slack_final,
                con=con_final,
                success=bool(resultado_scipy.success)
            )

        except ValueError as e:
            return RespuestaSciPyPL(
                estado=EstadoProblema.ERROR_VALIDACION_ENTRADA,
                mensaje=f"{EstadoProblema.ERROR_VALIDACION_ENTRADA.value} Detalles: {e}",
                x=None,
                fun=None,
                status=-1,
                message=str(e),
                nit=0,
                slack=None,
                con=None,
                success=False
            )
        except Exception as e:
            return RespuestaSciPyPL(
                estado=EstadoProblema.ERROR_SISTEMA_INTERNO,
                mensaje=f"{EstadoProblema.ERROR_SISTEMA_INTERNO.value} Detalles: {e}",
                x=None,
                fun=None,
                status=-1,
                message=str(e),
                nit=0,
                slack=None,
                con=None,
                success=False
            )

    # ------------------------------------------------------------------
    # Métodos privados de transformación
    # ------------------------------------------------------------------

    def _preparar_objetivo(self, problema: ProblemaPL) -> None:
        """
        Determina la dirección de optimización y convierte los coeficientes
        algebraicos a flotantes puros para procesamiento matricial en C/C++.
        """
        self._es_max = (problema.tipo == TipoOptimizacion.MAX)
        
        # Extracción segura de coeficientes desde la lista tipada del objeto problema
        coeficientes_float = [float(c) for c in problema.objetivo]
        c = np.array(coeficientes_float, dtype=np.float64)

        if self._es_max:
            c = -c  # Inversión matemática formal: max Z(x) == min -Z(x)

        self._c = c

    def _preparar_restricciones(self, problema: ProblemaPL) -> None:
        """
        Procesa el conjunto de restricciones del objeto problema y las segrega
        en hiperplanos de igualdad o desigualdad numéricas.
        """
        self._A_ub = []
        self._b_ub = []
        self._A_eq = []
        self._b_eq = []

        for restriccion in problema.restricciones:
            coefs = np.array([float(c) for c in restriccion.coeficientes], dtype=np.float64)
            rhs = float(restriccion.rhs)

            # Clasificación funcional basándose en los Enums tipados de la restricción
            if restriccion.signo == SignoRestriccion.MENOR_IGUAL:
                self._A_ub.append(coefs)
                self._b_ub.append(rhs)

            elif restriccion.signo == SignoRestriccion.MAYOR_IGUAL:
                # Multiplicación por escalar negativo para invertir el sentido lineal
                self._A_ub.append(-coefs)
                self._b_ub.append(-rhs)

            elif restriccion.signo == SignoRestriccion.IGUAL:
                self._A_eq.append(coefs)
                self._b_eq.append(rhs)

    def _construir_matrices(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """Compila las estructuras dinámicas a arreglos ndarray de NumPy."""
        A_ub = np.array(self._A_ub, dtype=np.float64) if self._A_ub else None
        b_ub = np.array(self._b_ub, dtype=np.float64) if self._b_ub else None
        A_eq = np.array(self._A_eq, dtype=np.float64) if self._A_eq else None
        b_eq = np.array(self._b_eq, dtype=np.float64) if self._b_eq else None
        return A_ub, b_ub, A_eq, b_eq

    def _construir_bounds(self) -> List[Tuple[float, Optional[float]]]:
        """Aplica la condición canónica clásica de no-negatividad para las variables."""
        return [(0.0, None)] * (len(self._c) if self._c is not None else 0)

    def _mapear_codigo_scipy(self, status: int) -> EstadoProblema:
        """Mapea de forma determinista el código numérico de SciPy a nuestro Enum semántico."""
        mapeo = {
            0: EstadoProblema.OPTIMO,
            1: EstadoProblema.LIMITE_ITERACIONES,
            2: EstadoProblema.INVIABLE,
            3: EstadoProblema.NO_ACOTADO,
            4: EstadoProblema.DIFICULTADES_NUMERICAS
        }
        return mapeo.get(status, EstadoProblema.ERROR_SISTEMA_INTERNO)