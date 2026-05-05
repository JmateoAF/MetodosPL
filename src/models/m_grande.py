"""
gran_m.py
=========
Módulo de backend para la resolución paso a paso de problemas de
Programación Lineal mediante el Método de la M Grande (Big M Method).

Restricciones de diseño:
    - Sin GUI, sin prints, sin scipy.
    - Todo el álgebra se realiza con fractions.Fraction para exactitud.
    - Las matrices NumPy usan dtype=object para alojar Fraction.
    - M se representa como Fraction(10**9, 1), nunca como float("inf").
    - Pensado para software educativo: expone cada iteración completa.

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
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Tipos de alias
# ---------------------------------------------------------------------------
Tableau = np.ndarray   # dtype=object, valores Fraction


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class SolucionadorGranM:
    """
    Implementa el método de la M Grande tabular paso a paso.

    Soporta:
        - Restricciones <=, >= y ==.
        - Problemas MAX y MIN.
        - Aritmética exacta con Fraction.
        - Historial completo de iteraciones para la Vista.

    Uso desde el Controlador:
        solver = SolucionadorGranM()
        resultado = solver.resolver(datos_entrada)
    """

    MAX_ITERACIONES: int = 300

    def __init__(self) -> None:
        self.M: Fraction = Fraction(10 ** 9, 1)   # penalización Big-M

        # Estado interno — reiniciado en cada llamada a resolver()
        self._n_vars: int = 0            # variables de decisión originales
        self._n_holguras: int = 0        # vars de holgura/exceso
        self._n_artificiales: int = 0    # vars artificiales
        self._es_max: bool = True
        self._base: list[int] = []       # índice de columna de la var básica por restricción
        self._nombres_cols: list[str] = []   # encabezados de columnas (sin "Base")
        self._idx_artificiales: list[int] = []  # índices de columna de vars artificiales

    # ------------------------------------------------------------------
    # Punto de entrada público
    # ------------------------------------------------------------------

    def resolver(self, datos_entrada: dict) -> dict:
        """
        Resuelve el problema y devuelve el historial completo de iteraciones.

        Parámetros
        ----------
        datos_entrada : dict
            {
                "tipo": "MAX" | "MIN",
                "objetivo": [c1, c2, ...],
                "restricciones": [
                    {"coeficientes": [...], "signo": "<= | >= | ==", "rhs": valor},
                    ...
                ]
            }

        Retorna
        -------
        dict con las claves:
            "estado"             : "optimo" | "inviable" | "no_acotado"
            "z_optimo"           : Fraction | None
            "variables_decision" : list[Fraction] | None
            "encabezados"        : list[str]   — para la Vista (incluye "Base")
            "variables_base"     : list[str]   — var básica de cada restricción al final
            "iteraciones"        : list[dict]
        """
        # --- Reiniciar estado ---
        self._n_vars = len(datos_entrada["objetivo"])
        self._es_max = datos_entrada["tipo"].upper().strip() == "MAX"
        self._base = []
        self._idx_artificiales = []

        # --- Calcular cuántas vars auxiliares necesita cada restricción ---
        plan = self._planificar_variables(datos_entrada["restricciones"])

        # --- Construir encabezados y tableau inicial ---
        self._nombres_cols = self._construir_encabezados(plan)
        tableau = self._construir_tableau(datos_entrada, plan)

        # --- Algebraizar fila Z: eliminar coeficientes de vars artificiales ---
        tableau = self._algebraizar_fila_z(tableau)

        # --- Ejecutar iteraciones Simplex ---
        return self._iterar(tableau)

    # ------------------------------------------------------------------
    # Planificación de variables auxiliares
    # ------------------------------------------------------------------

    def _planificar_variables(self, restricciones: list[dict]) -> list[dict]:
        """
        Para cada restricción determina qué variables auxiliares necesita:

            <=  →  holgura S  (coef +1 en la restricción, 0 en Z)
            >=  →  exceso S   (coef -1) + artificial A (coef +1, coef +M en Z)
            ==  →  artificial A (coef +1, coef +M en Z)

        Retorna una lista de dicts con la info de cada restricción.
        """
        col_aux = self._n_vars   # las columnas auxiliares empiezan después de Xn
        plan: list[dict] = []

        n_holguras = 0
        n_artificiales = 0

        for r in restricciones:
            signo = r["signo"].strip()
            entrada: dict[str, Any] = {"signo": signo, "holgura": None, "artificial": None}

            if signo == "<=":
                entrada["holgura"] = col_aux   # columna de la holgura
                col_aux += 1
                n_holguras += 1

            elif signo == ">=":
                entrada["holgura"] = col_aux   # columna del exceso (coef -1)
                col_aux += 1
                n_holguras += 1
                entrada["artificial"] = col_aux
                self._idx_artificiales.append(col_aux)
                col_aux += 1
                n_artificiales += 1

            elif signo == "==":
                entrada["artificial"] = col_aux
                self._idx_artificiales.append(col_aux)
                col_aux += 1
                n_artificiales += 1

            else:
                raise ValueError(f"Signo desconocido: '{signo}'. Use '<=', '>=' o '=='.")

            plan.append(entrada)

        self._n_holguras = n_holguras
        self._n_artificiales = n_artificiales
        return plan

    # ------------------------------------------------------------------
    # Encabezados de columnas
    # ------------------------------------------------------------------

    def _construir_encabezados(self, plan: list[dict]) -> list[str]:
        """
        Genera los nombres de columnas en el orden interno:
            X1…Xn | S1…Sk | A1…Ap | RHS

        Las holguras y excesos comparten el prefijo S;
        las artificiales usan el prefijo A.
        """
        cols: list[str] = [f"X{i+1}" for i in range(self._n_vars)]

        # Recorrer el plan para respetar el orden de asignación de columnas
        conteo_s = 1
        conteo_a = 1
        # Necesitamos mapear índice de columna → nombre; usamos un dict temporal
        mapa: dict[int, str] = {}

        for entrada in plan:
            if entrada["holgura"] is not None:
                mapa[entrada["holgura"]] = f"S{conteo_s}"
                conteo_s += 1
            if entrada["artificial"] is not None:
                mapa[entrada["artificial"]] = f"A{conteo_a}"
                conteo_a += 1

        # Ordenar por índice de columna para mantener el orden correcto
        for col_idx in sorted(mapa.keys()):
            cols.append(mapa[col_idx])

        cols.append("RHS")
        return cols

    # ------------------------------------------------------------------
    # Construcción del tableau inicial
    # ------------------------------------------------------------------

    def _construir_tableau(self, datos: dict, plan: list[dict]) -> Tableau:
        """
        Construye la tabla completa:

            Fila 0    : función objetivo Z con coeficientes de penalización
            Filas 1…m : restricciones estandarizadas

        Para MAX: los coeficientes de las Xj en Z son -Cj (se busca hacer Z crecer
                    restando los negativos).  Las artificiales se penalizan con +M
                    (en la fila Z sin algebraizar; eso se corrige después).
        Para MIN: igual pero se trabaja directamente con +Cj. Artificiales con +M.
        """
        m = len(datos["restricciones"])
        total_cols = len(self._nombres_cols)   # incluye RHS
        total_filas = m + 1                    # fila Z + restricciones

        T: Tableau = np.full((total_filas, total_cols), Fraction(0), dtype=object)

        # ── Fila 0: función objetivo ──────────────────────────────────
        signo_z = Fraction(1) if self._es_max else Fraction(-1)
        for j, c in enumerate(datos["objetivo"]):
            # MAX: almacenamos -Cj  (condición de optimalidad: todos >= 0)
            T[0, j] = Fraction(-c) * signo_z

        # Penalización +M para cada variable artificial en la fila Z
        # (antes de algebraizar; los valores reales se corregirán en
        #  _algebraizar_fila_z restando M * fila_restricción)
        for idx_col in self._idx_artificiales:
            T[0, idx_col] = self.M

        # ── Filas 1…m: restricciones ──────────────────────────────────
        for i, (r, entrada) in enumerate(zip(datos["restricciones"], plan)):
            fila = i + 1   # fila 0 es Z

            # Coeficientes de las variables de decisión
            for j, coef in enumerate(r["coeficientes"]):
                T[fila, j] = Fraction(coef)

            # Variable de holgura o exceso
            if entrada["holgura"] is not None:
                coef_holgura = Fraction(1) if entrada["signo"] == "<=" else Fraction(-1)
                T[fila, entrada["holgura"]] = coef_holgura

            # Variable artificial
            if entrada["artificial"] is not None:
                T[fila, entrada["artificial"]] = Fraction(1)

            # RHS
            T[fila, -1] = Fraction(r["rhs"])

        # ── Vector de base inicial ────────────────────────────────────
        # La variable básica de cada restricción es:
        #   - La holgura S  si el signo es <=
        #   - La artificial A  si el signo es >= o ==
        for i, entrada in enumerate(plan):
            if entrada["signo"] == "<=":
                self._base.append(entrada["holgura"])
            else:
                self._base.append(entrada["artificial"])

        return T

    # ------------------------------------------------------------------
    # Algebraización inicial de la fila Z
    # ------------------------------------------------------------------

    def _algebraizar_fila_z(self, T: Tableau) -> Tableau:
        """
        Elimina los coeficientes no nulos de las variables artificiales
        en la fila Z mediante operaciones de fila:

            Fila_Z  ←  Fila_Z  -  M * Fila_restricción_i
                (para cada restricción i cuya variable básica sea artificial)

        Esto garantiza que las columnas de las variables básicas iniciales
        tengan cero en la fila Z, cumpliendo la forma canónica del Simplex.
        """
        T = T.copy()
        m = len(self._base)

        for i, col_base in enumerate(self._base):
            if col_base in self._idx_artificiales:
                fila_restr = i + 1   # +1 porque fila 0 es Z
                factor = T[0, col_base]   # coeficiente de la artificial en Z
                if factor != Fraction(0):
                    T[0, :] = [
                        T[0, k] - factor * T[fila_restr, k]
                        for k in range(T.shape[1])
                    ]

        return T

    # ------------------------------------------------------------------
    # Bucle de iteraciones Simplex
    # ------------------------------------------------------------------

    def _iterar(self, tableau: Tableau) -> dict:
        """
        Ejecuta el Simplex estándar sobre el tableau penalizado.

        En cada ciclo:
            1. Busca columna pivote (más negativo en fila Z).
            2. Busca fila pivote (prueba del cociente mínimo, filas 1…m).
            3. Guarda snapshot ANTES del pivoteo.
            4. Pivotea y actualiza la base.
        """
        iteraciones: list[dict] = []
        m = len(self._base)

        for _ in range(self.MAX_ITERACIONES):

            # 1. ¿Óptimo?
            col_pivote = self._columna_pivote(tableau)
            if col_pivote is None:
                iteraciones.append(
                    self._snapshot(tableau, None, None, "Solución óptima encontrada.")
                )
                return self._construir_resultado("optimo", tableau, iteraciones)

            # 2. ¿No acotado?
            fila_pivote = self._fila_pivote(tableau, col_pivote)
            if fila_pivote is None:
                iteraciones.append(
                    self._snapshot(tableau, None, col_pivote,
                                    "Problema no acotado: no existe cociente mínimo.")
                )
                return self._construir_resultado("no_acotado", tableau, iteraciones)

            # 3. Snapshot antes del pivoteo
            var_entra = self._nombres_cols[col_pivote]
            var_sale  = self._nombres_cols[self._base[fila_pivote - 1]]
            mensaje   = f"Entra {var_entra}, sale {var_sale}."
            iteraciones.append(
                self._snapshot(tableau, fila_pivote, col_pivote, mensaje)
            )

            # 4. Pivotear y actualizar base
            tableau = self._pivotear(tableau, fila_pivote, col_pivote)
            self._base[fila_pivote - 1] = col_pivote

        # Límite de iteraciones agotado
        iteraciones.append(
            self._snapshot(tableau, None, None, "Límite de iteraciones alcanzado.")
        )
        return self._construir_resultado("no_acotado", tableau, iteraciones)

    # ------------------------------------------------------------------
    # Selección de pivotes
    # ------------------------------------------------------------------

    def _columna_pivote(self, T: Tableau) -> int | None:
        """
        Columna pivote: coeficiente más negativo en la fila Z (sin RHS).
        Retorna None si todos son >= 0 (condición de optimalidad).
        """
        fila_z = T[0, :-1]
        min_val = Fraction(0)
        col_pivote = None

        for j, val in enumerate(fila_z):
            if val < min_val:
                min_val = val
                col_pivote = j

        return col_pivote

    def _fila_pivote(self, T: Tableau, col_pivote: int) -> int | None:
        """
        Prueba del cociente mínimo sobre las filas de restricción (1…m).
        Solo considera filas con elemento positivo en la columna pivote.
        Retorna None si no hay cociente válido (problema no acotado).
        """
        m = len(self._base)
        min_ratio: Fraction | None = None
        fila_pivote: int | None = None

        for i in range(1, m + 1):
            elemento = T[i, col_pivote]
            if elemento > Fraction(0):
                ratio = T[i, -1] / elemento
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    fila_pivote = i

        return fila_pivote

    # ------------------------------------------------------------------
    # Operación de pivoteo
    # ------------------------------------------------------------------

    def _pivotear(self, T: Tableau, fila_p: int, col_p: int) -> Tableau:
        """
        Convierte la columna pivote en vector canónico mediante operaciones
        de fila exactas con Fraction. Retorna una nueva copia del tableau.
        """
        T = T.copy()
        pivote = T[fila_p, col_p]

        # Normalizar fila pivote
        T[fila_p, :] = [v / pivote for v in T[fila_p, :]]

        # Eliminar en todas las demás filas (incluida la fila Z)
        for i in range(T.shape[0]):
            if i != fila_p:
                factor = T[i, col_p]
                if factor != Fraction(0):
                    T[i, :] = [
                        T[i, k] - factor * T[fila_p, k]
                        for k in range(T.shape[1])
                    ]

        return T

    # ------------------------------------------------------------------
    # Construcción de snapshots y resultado final
    # ------------------------------------------------------------------

    def _snapshot(
        self,
        T: Tableau,
        fila_pivote: int | None,
        col_pivote: int | None,
        mensaje: str,
    ) -> dict:
        """
        Captura el estado del tableau para la Vista.

        Antepone una columna "Base" con la variable básica de cada fila:
            Fila 0 → "Z"
            Fila i → nombre de la variable básica de la restricción i-1
        """
        m = len(self._base)
        n_filas, n_data_cols = T.shape

        # Columna de base
        col_base: list[str] = ["Z"] + [self._nombres_cols[self._base[i]] for i in range(m)]

        # Ensamblar tabla completa con columna base al inicio
        tabla_completa = np.empty((n_filas, n_data_cols + 1), dtype=object)
        for i in range(n_filas):
            tabla_completa[i, 0] = col_base[i]
            for j in range(n_data_cols):
                tabla_completa[i, j + 1] = T[i, j]

        return {
            "tabla"      : tabla_completa,
            "fila_pivote": fila_pivote,
            "col_pivote" : col_pivote,
            "mensaje"    : mensaje,
        }

    def _construir_resultado(
        self,
        estado: str,
        T: Tableau,
        iteraciones: list[dict],
    ) -> dict:
        """
        Ensambla el diccionario de salida final.

        Verifica si quedan variables artificiales en la base para declarar
        el problema como inviable.

        El valor Z se extrae de T[0, -1] y se re-invierte para MIN.
        """
        n = self._n_vars
        m = len(self._base)

        z_optimo: Fraction | None = None
        variables_decision: list[Fraction] | None = None

        # ── Detectar inviabilidad ─────────────────────────────────────
        # Si alguna variable artificial permanece en la base con valor > 0,
        # el problema no tiene solución factible.
        if estado == "optimo":
            artificiales_en_base = [
                col for col in self._base if col in self._idx_artificiales
            ]
            for col in artificiales_en_base:
                idx_restr = self._base.index(col)
                if T[idx_restr + 1, -1] > Fraction(0):
                    estado = "inviable"
                    break

        if estado == "optimo":
            # Valor Z real (fila 0, columna RHS)
            z_raw = T[0, -1]
            z_optimo = z_raw if self._es_max else -z_raw

            # Valores de las variables de decisión desde la base
            variables_decision = []
            for j in range(n):
                if j in self._base:
                    idx = self._base.index(j)
                    variables_decision.append(T[idx + 1, -1])   # +1: fila 0 es Z
                else:
                    variables_decision.append(Fraction(0))

        # Encabezados completos para la Vista
        encabezados_vista = ["Base"] + self._nombres_cols

        # Variable básica de cada restricción al final
        variables_base = [self._nombres_cols[self._base[i]] for i in range(m)]

        return {
            "estado"             : estado,
            "z_optimo"           : z_optimo,
            "variables_decision" : variables_decision,
            "encabezados"        : encabezados_vista,
            "variables_base"     : variables_base,
            "iteraciones"        : iteraciones,
        }
