# src/models/metodos/m_grande.py
"""
Módulo de backend para la resolución paso a paso de problemas de
Programación Lineal mediante el Método de la M Grande (Big M Method).

Restricciones de diseño:
    - Orientación a Objetos pura y Tipado Estático Estricto.
    - Sin diccionarios, sin prints, sin scipy, sin usar hasattr.
    - Todo el álgebra se realiza con fractions.Fraction para exactitud.
    - Las matrices NumPy usan dtype=object para alojar Fraction.
    - M se representa como Fraction(10**9, 1), nunca como float("inf").

Orden de filas en el tableau:
    Fila 0        : función objetivo Z  (SIEMPRE)
    Fila 1 … m    : restricciones estandarizadas

Orden de columnas en el tableau:
    [X1…Xn | S1…Sk | A1…Ap | RHS]
    donde n = vars de decisión, k = vars de holgura/exceso, p = vars artificiales.

Autor: Backend Module — MVC Gran M Optimizer
"""

from __future__ import annotations
from fractions import Fraction
import numpy as np
from typing import List, Optional, Dict, Any

# Importaciones estrictas de las entidades de dominio orientadas a objetos
from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
from src.models.entity.programacion_lineal.respuesta import RespuestaTabularPL, IteracionTabular, NumericoTabular


class SolucionadorGranM:
    """
    Implementa el método de la M Grande tabular paso a paso utilizando objetos de dominio.
    """

    MAX_ITERACIONES: int = 300

    def __init__(self) -> None:
        """Inicializa las variables estructurales del solucionador con la penalización Big-M."""
        self.M: Fraction = Fraction(10 ** 9, 1)   # Penalización Big-M

        # Estado interno — reiniciado en cada llamada a resolver()
        self._n_vars: int = 0            # Variables de decisión originales
        self._n_holguras: int = 0        # Variables de holgura/exceso
        self._n_artificiales: int = 0    # Variables artificiales
        self._es_max: bool = True        # Bandera para determinar si es Maximización
        self._base: List[int] = []       # Índice de columna de la variable básica por restricción
        self._nombres_cols: List[str] = []   # Encabezados de columnas (sin incluir "Base")
        self._idx_artificiales: List[int] = []  # Índices de columna de variables artificiales

    def resolver(self, problema: ProblemaPL) -> RespuestaTabularPL:
        """
        Resuelve el problema de programación lineal mediante el método de la M Grande.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad inmutable que contiene el modelo matemático formal.

        Retorna
        -------
        RespuestaTabularPL
            Entidad inmutable con el resultado final y el historial de tableaus autodescriptivos.
        """
        # --- 1. Inicialización y extracción segura de atributos de dominio ---
        self._n_vars = problema.total_variables
        self._es_max = (problema.tipo == TipoOptimizacion.MAX)
        self._base = []
        self._idx_artificiales = []

        # --- 2. Calcular cuántas variables auxiliares necesita cada restricción ---
        plan = self._planificar_variables(problema.restricciones)

        # --- 3. Construir encabezados y tableau inicial ---
        self._nombres_cols = self._construir_encabezados(plan)
        tableau = self._construir_tableau(problema, plan)

        # --- 4. Algebraizar fila Z: eliminar coeficientes de variables artificiales ---
        tableau = self._algebraizar_fila_z(tableau)

        # --- 5. Ejecutar iteraciones Simplex ---
        return self._iterar(tableau)

    def _planificar_variables(self, restricciones: List[Restriccion]) -> List[Dict[str, Any]]:
        """
        Para cada restricción determina qué variables auxiliares necesita.
        Retorna una lista de diccionarios de control interno con la información de indexación.
        """
        col_aux = self._n_vars   # Las columnas auxiliares empiezan después de las variables de decisión originales
        plan: List[Dict[str, Any]] = []

        n_holguras = 0
        n_artificiales = 0

        for r in restricciones:
            entrada: Dict[str, Any] = {"signo": r.signo, "holgura": None, "artificial": None}

            if r.signo == SignoRestriccion.MENOR_IGUAL:
                entrada["holgura"] = col_aux
                col_aux += 1
                n_holguras += 1
            elif r.signo == SignoRestriccion.MAYOR_IGUAL:
                entrada["holgura"] = col_aux   # Columna del exceso (coeficiente -1)
                col_aux += 1
                n_holguras += 1
                entrada["artificial"] = col_aux
                self._idx_artificiales.append(col_aux)
                col_aux += 1
                n_artificiales += 1
            elif r.signo == SignoRestriccion.IGUAL:
                entrada["artificial"] = col_aux
                self._idx_artificiales.append(col_aux)
                col_aux += 1
                n_artificiales += 1
            
            plan.append(entrada)
        
        self._n_holguras = n_holguras
        self._n_artificiales = n_artificiales
        return plan

    def _construir_encabezados(self, plan: List[Dict[str, Any]]) -> List[str]:
        """Genera los nombres de columnas en el orden interno exacto."""
        cols: List[str] = [f"X{i+1}" for i in range(self._n_vars)]

        conteo_s = 1
        conteo_a = 1
        mapa_temporal: Dict[int, str] = {}

        for entrada in plan:
            if entrada["holgura"] is not None:
                mapa_temporal[entrada["holgura"]] = f"S{conteo_s}"
                conteo_s += 1
            if entrada["artificial"] is not None:
                mapa_temporal[entrada["artificial"]] = f"A{conteo_a}"
                conteo_a += 1

        for col_idx in sorted(mapa_temporal.keys()):
            cols.append(mapa_temporal[col_idx])

        cols.append("RHS")
        return cols

    def _construir_tableau(self, problema: ProblemaPL, plan: List[Dict[str, Any]]) -> np.ndarray:
        """Construye la matriz inicial aplicando las penalizaciones Big-M correspondientes."""
        m = problema.total_restricciones
        total_cols = len(self._nombres_cols)
        total_filas = m + 1

        T = np.full((total_filas, total_cols), Fraction(0), dtype=object)

        # --- Fila 0: función objetivo Z ---
        signo_z = Fraction(1) if self._es_max else Fraction(-1)
        for j, c in enumerate(problema.objetivo):
            T[0, j] = Fraction(-c) * signo_z

        # Penalización +M inicial para cada variable artificial en la fila Z
        for idx_col in self._idx_artificiales:
            T[0, idx_col] = self.M

        # --- Filas 1…m: restricciones ---
        for i, (r, entrada) in enumerate(zip(problema.restricciones, plan)):
            fila = i + 1

            for j, coef in enumerate(r.coeficientes):
                T[fila, j] = Fraction(coef)

            if entrada["holgura"] is not None:
                coef_holgura = Fraction(1) if entrada["signo"] == SignoRestriccion.MENOR_IGUAL else Fraction(-1)
                T[fila, entrada["holgura"]] = coef_holgura

            if entrada["artificial"] is not None:
                T[fila, entrada["artificial"]] = Fraction(1)

            T[fila, -1] = Fraction(r.rhs)

        # --- Inicializar vector de base ---
        for entrada in plan:
            if entrada["signo"] == SignoRestriccion.MENOR_IGUAL:
                self._base.append(entrada["holgura"])
            else:
                self._base.append(entrada["artificial"])

        return T

    def _algebraizar_fila_z(self, T: np.ndarray) -> np.ndarray:
        """Elimina las M de las variables artificiales básicas para lograr la forma canónica."""
        T = T.copy()

        for i, col_base in enumerate(self._base):
            if col_base in self._idx_artificiales:
                fila_restr = i + 1
                factor = T[0, col_base]
                if factor != Fraction(0):
                    T[0, :] = [T[0, k] - factor * T[fila_restr, k] for k in range(T.shape[1])]

        return T

    def _iterar(self, tableau: np.ndarray) -> RespuestaTabularPL:
        """Ejecuta el bucle del algoritmo Simplex penalizado registrando estados inmutables."""
        iteraciones: List[IteracionTabular] = []

        for _ in range(self.MAX_ITERACIONES):
            # 1. Condición de optimalidad
            col_pivote = self._columna_pivote(tableau)
            if col_pivote is None:
                iteraciones.append(self._crear_snapshot(tableau, None, None, "Solución óptima encontrada."))
                return self._construir_resultado(EstadoProblema.OPTIMO, tableau, iteraciones)

            # 2. Condición de acotamiento
            fila_pivote = self._fila_pivote(tableau, col_pivote)
            if fila_pivote is None:
                iteraciones.append(self._crear_snapshot(tableau, None, col_pivote, "Problema no acotado: no existe cociente mínimo."))
                return RespuestaTabularPL(
                    estado=EstadoProblema.NO_ACOTADO,
                    mensaje=EstadoProblema.NO_ACOTADO.value,
                    iteraciones=iteraciones
                )

            # 3. Snapshot antes del pivoteo
            var_entra = self._nombres_cols[col_pivote]
            var_sale = self._nombres_cols[self._base[fila_pivote - 1]]
            mensaje_pivote = f"Entra {var_entra}, sale {var_sale}."
            iteraciones.append(self._crear_snapshot(tableau, fila_pivote, col_pivote, mensaje_pivote))

            # 4. Pivotear y actualizar base
            tableau = self._pivotear(tableau, fila_pivote, col_pivote)
            self._base[fila_pivote - 1] = col_pivote

        # Límite alcanzado sin convergencia
        iteraciones.append(self._crear_snapshot(tableau, None, None, "Límite de iteraciones alcanzado."))
        return RespuestaTabularPL(
            estado=EstadoProblema.LIMITE_ITERACIONES,
            mensaje=EstadoProblema.LIMITE_ITERACIONES.value,
            iteraciones=iteraciones
        )

    def _columna_pivote(self, T: np.ndarray) -> Optional[int]:
        """Selecciona la columna con el costo reducido más negativo."""
        fila_z = T[0, :-1]
        min_val = Fraction(0)
        col_pivote = None

        for j, val in enumerate(fila_z):
            if val < min_val:
                min_val = val
                col_pivote = j

        return col_pivote

    def _fila_pivote(self, T: np.ndarray, col_pivote: int) -> Optional[int]:
        """Aplica la prueba del cociente mínimo para determinar la variable de salida."""
        m = len(self._base)
        min_ratio: Optional[Fraction] = None
        fila_pivote: Optional[int] = None

        for i in range(1, m + 1):
            elemento = T[i, col_pivote]
            if elemento > Fraction(0):
                ratio = T[i, -1] / elemento
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    fila_pivote = i

        return fila_pivote

    def _pivotear(self, T: np.ndarray, fila_p: int, col_p: int) -> np.ndarray:
        """Genera una nueva matriz aplicando eliminación de Gauss-Jordan exacta."""
        T = T.copy()
        pivote = T[fila_p, col_p]

        T[fila_p, :] = [v / pivote for v in T[fila_p, :]]

        for i in range(T.shape[0]):
            if i != fila_p:
                factor = T[i, col_p]
                if factor != Fraction(0):
                    T[i, :] = [T[i, k] - factor * T[fila_p, k] for k in range(T.shape[1])]

        return T

    def _crear_snapshot(self, T: np.ndarray, fila_p: Optional[int], col_p: Optional[int], mensaje: str) -> IteracionTabular:
        """Construye una instancia inmutable de IteracionTabular anteponiendo la columna 'Base'."""
        m = len(self._base)
        n_filas, n_data_cols = T.shape

        variables_base_actuales: List[str] = [self._nombres_cols[self._base[i]] for i in range(m)]
        col_base: List[str] = ["Z"] + variables_base_actuales

        tabla_completa = np.empty((n_filas, n_data_cols + 1), dtype=object)
        for i in range(n_filas):
            tabla_completa[i, 0] = col_base[i]
            for j in range(n_data_cols):
                tabla_completa[i, j + 1] = T[i, j]

        return IteracionTabular(
            tabla=tabla_completa,
            encabezados=["Base"] + self._nombres_cols,
            variables_base=variables_base_actuales,
            mensaje=mensaje,
            fila_pivote=fila_p,
            col_pivote=col_p,
            fase=None
        )

    def _construir_resultado(self, estado: EstadoProblema, T: np.ndarray, iteraciones: List[IteracionTabular]) -> RespuestaTabularPL:
        """Evalúa las artificiales en la base para detectar infactibilidad y genera la RespuestaTabularPL final."""
        n = self._n_vars
        m = len(self._base)

        z_optimo: Optional[Fraction] = None
        variables_decision: List[NumericoTabular] = []

        # --- Detectar inviabilidad analítica ---
        # Si una variable artificial sigue en la base con valor mayor que cero, la región es vacía.
        if estado == EstadoProblema.OPTIMO:
            artificiales_en_base = [col for col in self._base if col in self._idx_artificiales]
            for col in artificiales_en_base:
                idx_restr = self._base.index(col)
                if T[idx_restr + 1, -1] > Fraction(0):
                    estado = EstadoProblema.INVIABLE
                    break

        if estado == EstadoProblema.OPTIMO:
            z_raw = T[0, -1]
            z_optimo = z_raw if self._es_max else -z_raw

            for j in range(n):
                if j in self._base:
                    idx = self._base.index(j)
                    variables_decision.append(T[idx + 1, -1])
                else:
                    variables_decision.append(Fraction(0))
        else:
            variables_decision = [Fraction(0)] * n

        return RespuestaTabularPL(
            estado=estado,
            mensaje=estado.value,
            z_optimo=z_optimo,
            variables_decision=variables_decision,
            iteraciones=iteraciones
        )
