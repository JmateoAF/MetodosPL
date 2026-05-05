"""
dos_fases.py
============
Módulo de backend para la resolución paso a paso de problemas de
Programación Lineal mediante el Método de las Dos Fases (Two-Phase Simplex).

Restricciones de diseño:
    - Sin GUI, sin prints, sin scipy.
    - Todo el álgebra se realiza con fractions.Fraction para exactitud exacta.
    - Las matrices NumPy usan dtype=object para alojar Fraction.
    - Fila 0 es SIEMPRE la función objetivo (W en Fase 1, Z en Fase 2).
    - Pensado para software educativo: expone cada iteración de ambas fases.

Orden de filas en cualquier tableau:
    Fila 0        : función objetivo (W o Z)
    Fila 1 … m    : restricciones estandarizadas

Orden de columnas en Fase 1:
    [X1…Xn | S1…Sk | A1…Ap | RHS]

Orden de columnas en Fase 2 (artificiales eliminadas):
    [X1…Xn | S1…Sk | RHS]

Autor: Backend Module — MVC Two-Phase Simplex Optimizer
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Alias de tipo
# ---------------------------------------------------------------------------
Tableau = np.ndarray   # dtype=object, valores Fraction


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class SolucionadorDosFases:
    """
    Implementa el Método de las Dos Fases tabular, paso a paso.

    Fase 1 — Minimiza W = ΣAi para encontrar una BFS inicial.
    Fase 2 — Optimiza Z original eliminando las artificiales.

    Soporta restricciones <=, >= y ==, y problemas MAX/MIN.

    Uso desde el Controlador:
        solver = SolucionadorDosFases()
        resultado = solver.resolver(datos_entrada)
    """

    MAX_ITERACIONES: int = 300

    def __init__(self) -> None:
        # ── Dimensiones del problema ───────────────────────────────────
        self._n_vars: int = 0
        self._n_restricciones: int = 0
        self._n_holguras: int = 0
        self._n_artificiales: int = 0

        # ── Metadatos del problema ─────────────────────────────────────
        self._es_max: bool = True
        self._objetivo_original: list[Fraction] = []

        # ── Estado del tableau ─────────────────────────────────────────
        self._base: list[int] = []

        # ── Nombres de columnas ────────────────────────────────────────
        self._nombres_f1: list[str] = []
        self._nombres_f2: list[str] = []

        # ── Índices de las artificiales en el tableau de Fase 1 ───────
        self._idx_artificiales_f1: list[int] = []

        # ── Mapa de reindexación Fase 1 → Fase 2 ──────────────────────
        self._mapa_col: dict[int, int | None] = {}

    # ══════════════════════════════════════════════════════════════════
    # PUNTO DE ENTRADA PÚBLICO
    # ══════════════════════════════════════════════════════════════════

    def resolver(self, datos_entrada: dict) -> dict:
        """
        Resuelve el problema completo y devuelve el historial de ambas fases.
        """
        # --- Reiniciar estado interno ---
        self._n_vars = len(datos_entrada["objetivo"])
        self._n_restricciones = len(datos_entrada["restricciones"])
        self._es_max = datos_entrada["tipo"].upper().strip() == "MAX"
        self._objetivo_original = [Fraction(c) for c in datos_entrada["objetivo"]]

        self._base = []
        self._idx_artificiales_f1 = []
        self._mapa_col = {}

        # --- Planificar variables auxiliares ---
        plan = self._planificar_variables(datos_entrada["restricciones"])

        # --- Construir encabezados y tableau de Fase 1 ---
        self._nombres_f1 = self._construir_encabezados_f1(plan)
        tableau_f1 = self._construir_tableau_f1(datos_entrada, plan)

        # --- Algebraizar fila W (fila 0) de Fase 1 ---
        tableau_f1 = self._algebraizar_fila_w(tableau_f1)

        # ── FASE 1 ────────────────────────────────────────────────────
        resultado_f1, iteraciones_f1, tableau_f1_final = self._ejecutar_fase(
            tableau_f1, fase=1
        )

        if resultado_f1 == "inviable" or (tableau_f1_final is not None and tableau_f1_final[0, -1] < Fraction(0)):
            return self._respuesta(
                estado="inviable",
                iteraciones=iteraciones_f1,
                tableau_final=None,
            )

        if resultado_f1 == "no_acotado":
            return self._respuesta(
                estado="no_acotado",
                iteraciones=iteraciones_f1,
                tableau_final=None,
            )

        # ── FASE 2 ────────────────────────────────────────────────────
        tableau_f2 = self._construir_tableau_f2(tableau_f1_final)
        tableau_f2 = self._algebraizar_fila_z(tableau_f2)

        resultado_f2, iteraciones_f2, tableau_f2_final = self._ejecutar_fase(
            tableau_f2, fase=2
        )

        iteraciones_totales = iteraciones_f1 + iteraciones_f2

        if resultado_f2 == "no_acotado":
            return self._respuesta(
                estado="no_acotado",
                iteraciones=iteraciones_totales,
                tableau_final=None,
            )

        return self._respuesta(
            estado="optimo",
            iteraciones=iteraciones_totales,
            tableau_final=tableau_f2_final,
        )

    # ══════════════════════════════════════════════════════════════════
    # PLANIFICACIÓN Y CONSTRUCCIÓN DEL TABLEAU DE FASE 1
    # ══════════════════════════════════════════════════════════════════

    def _planificar_variables(self, restricciones: list[dict]) -> list[dict]:
        col = self._n_vars
        plan: list[dict] = []
        n_holguras = 0
        n_artificiales = 0

        for r in restricciones:
            signo = r["signo"].strip()
            if signo not in ("<=", ">=", "=="):
                raise ValueError(f"Signo '{signo}' no reconocido. Use '<=', '>=' o '=='.")

            entrada: dict[str, Any] = {
                "signo"     : signo,
                "holgura"   : None,
                "artificial": None,
            }

            if signo == "<=":
                entrada["holgura"] = col
                col += 1
                n_holguras += 1

            elif signo == ">=":
                entrada["holgura"] = col        # exceso (coef -1)
                col += 1
                n_holguras += 1
                entrada["artificial"] = col
                self._idx_artificiales_f1.append(col)
                col += 1
                n_artificiales += 1

            elif signo == "==":
                entrada["artificial"] = col
                self._idx_artificiales_f1.append(col)
                col += 1
                n_artificiales += 1

            plan.append(entrada)

        self._n_holguras = n_holguras
        self._n_artificiales = n_artificiales
        return plan

    def _construir_encabezados_f1(self, plan: list[dict]) -> list[str]:
        cols: list[str] = [f"X{i+1}" for i in range(self._n_vars)]
        mapa: dict[int, str] = {}
        cs, ca = 1, 1

        for entrada in plan:
            if entrada["holgura"] is not None:
                mapa[entrada["holgura"]] = f"S{cs}"
                cs += 1
            if entrada["artificial"] is not None:
                mapa[entrada["artificial"]] = f"A{ca}"
                ca += 1

        for col_idx in sorted(mapa.keys()):
            cols.append(mapa[col_idx])

        cols.append("RHS")
        return cols

    def _construir_tableau_f1(self, datos: dict, plan: list[dict]) -> Tableau:
        m = self._n_restricciones
        total_cols = len(self._nombres_f1)
        total_filas = m + 1

        T: Tableau = np.full((total_filas, total_cols), Fraction(0), dtype=object)

        # ── Fila 0 (W): 1 en cada columna artificial ──────────────────
        for idx_col in self._idx_artificiales_f1:
            T[0, idx_col] = Fraction(1)

        # ── Filas 1…m: restricciones ──────────────────────────────────
        for i, (r, entrada) in enumerate(zip(datos["restricciones"], plan)):
            fila = i + 1
            for j, coef in enumerate(r["coeficientes"]):
                T[fila, j] = Fraction(coef)

            if entrada["holgura"] is not None:
                T[fila, entrada["holgura"]] = (
                    Fraction(1) if entrada["signo"] == "<=" else Fraction(-1)
                )

            if entrada["artificial"] is not None:
                T[fila, entrada["artificial"]] = Fraction(1)

            T[fila, -1] = Fraction(r["rhs"])

        # ── Base inicial ──────────────────────────────────────────────
        for entrada in plan:
            if entrada["signo"] == "<=":
                self._base.append(entrada["holgura"])
            else:
                self._base.append(entrada["artificial"])

        return T

    def _algebraizar_fila_w(self, T: Tableau) -> Tableau:
        T = T.copy()
        for i, col_base in enumerate(self._base):
            if col_base in self._idx_artificiales_f1:
                fila_restr = i + 1
                factor = T[0, col_base]
                if factor != Fraction(0):
                    T[0, :] = [
                        T[0, k] - factor * T[fila_restr, k]
                        for k in range(T.shape[1])
                    ]
        return T

    # ══════════════════════════════════════════════════════════════════
    # CONSTRUCCIÓN DEL TABLEAU DE FASE 2
    # ══════════════════════════════════════════════════════════════════

    def _construir_tableau_f2(self, T_f1: Tableau) -> Tableau:
        n_cols_f1 = T_f1.shape[1]

        nuevos_nombres: list[str] = []
        self._mapa_col = {}
        nuevo_idx = 0
        for j in range(n_cols_f1):
            nombre_j = self._nombres_f1[j]
            if j in self._idx_artificiales_f1:
                self._mapa_col[j] = None
            else:
                self._mapa_col[j] = nuevo_idx
                nuevos_nombres.append(nombre_j)
                nuevo_idx += 1

        self._nombres_f2 = nuevos_nombres

        n_cols_f2 = len(self._nombres_f2)
        m = self._n_restricciones
        T_f2: Tableau = np.full((m + 1, n_cols_f2), Fraction(0), dtype=object)

        for i in range(1, m + 1):
            for j_f1 in range(n_cols_f1):
                j_f2 = self._mapa_col[j_f1]
                if j_f2 is not None:
                    T_f2[i, j_f2] = T_f1[i, j_f1]

        signo_z = Fraction(1) if self._es_max else Fraction(-1)
        for j, c in enumerate(self._objetivo_original):
            T_f2[0, j] = Fraction(-c) * signo_z

        self._base = [self._mapa_col[col_f1] for col_f1 in self._base]

        return T_f2

    def _algebraizar_fila_z(self, T: Tableau) -> Tableau:
        T = T.copy()
        for i, col_base in enumerate(self._base):
            fila_restr = i + 1
            factor = T[0, col_base]
            if factor != Fraction(0):
                T[0, :] = [
                    T[0, k] - factor * T[fila_restr, k]
                    for k in range(T.shape[1])
                ]
        return T

    # ══════════════════════════════════════════════════════════════════
    # MOTOR SIMPLEX GENÉRICO
    # ══════════════════════════════════════════════════════════════════

    def _ejecutar_fase(self, tableau: Tableau, fase: int) -> tuple[str, list[dict], Tableau]:
        iteraciones: list[dict] = []
        nombres = self._nombres_f1 if fase == 1 else self._nombres_f2

        for _ in range(self.MAX_ITERACIONES):

            col_pivote = self._columna_pivote(tableau)
            if col_pivote is None:
                iteraciones.append(
                    self._snapshot(tableau, None, None,
                                    f"FASE {fase} — Óptimo alcanzado.", fase, nombres)
                )
                if fase == 1 and tableau[0, -1] > Fraction(0):
                    return "inviable", iteraciones, tableau
                return "optimo", iteraciones, tableau

            fila_pivote = self._fila_pivote(tableau, col_pivote)
            if fila_pivote is None:
                iteraciones.append(
                    self._snapshot(tableau, None, col_pivote,
                                    f"FASE {fase} — Problema no acotado.", fase, nombres)
                )
                return "no_acotado", iteraciones, tableau

            var_entra = nombres[col_pivote]
            var_sale  = nombres[self._base[fila_pivote - 1]]
            mensaje   = f"FASE {fase} — Entra {var_entra}, sale {var_sale}."
            iteraciones.append(
                self._snapshot(tableau, fila_pivote, col_pivote, mensaje, fase, nombres)
            )

            tableau = self._pivotear(tableau, fila_pivote, col_pivote)
            self._base[fila_pivote - 1] = col_pivote

        iteraciones.append(
            self._snapshot(tableau, None, None,
                            f"FASE {fase} — Límite de iteraciones alcanzado.", fase, nombres)
        )
        return "no_acotado", iteraciones, tableau

    # ══════════════════════════════════════════════════════════════════
    # OPERACIONES SOBRE EL TABLEAU
    # ══════════════════════════════════════════════════════════════════

    def _columna_pivote(self, T: Tableau) -> int | None:
        fila_obj = T[0, :-1]
        min_val = Fraction(0)
        col_pivote: int | None = None

        for j, val in enumerate(fila_obj):
            if val < min_val:
                min_val = val
                col_pivote = j

        return col_pivote

    def _fila_pivote(self, T: Tableau, col_pivote: int) -> int | None:
        m = self._n_restricciones
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

    def _pivotear(self, T: Tableau, fila_p: int, col_p: int) -> Tableau:
        T = T.copy()
        pivote = T[fila_p, col_p]

        T[fila_p, :] = [v / pivote for v in T[fila_p, :]]

        for i in range(T.shape[0]):
            if i != fila_p:
                factor = T[i, col_p]
                if factor != Fraction(0):
                    T[i, :] = [
                        T[i, k] - factor * T[fila_p, k]
                        for k in range(T.shape[1])
                    ]

        return T

    # ══════════════════════════════════════════════════════════════════
    # SNAPSHOTS Y RESULTADO FINAL
    # ══════════════════════════════════════════════════════════════════

    def _snapshot(
        self,
        T: Tableau,
        fila_pivote: int | None,
        col_pivote: int | None,
        mensaje: str,
        fase: int,
        nombres: list[str],
    ) -> dict:
        m = self._n_restricciones
        n_filas, n_data_cols = T.shape

        etiqueta_obj = "W" if fase == 1 else "Z"
        col_base: list[str] = [etiqueta_obj] + [
            nombres[self._base[i]] for i in range(m)
        ]

        tabla_completa = np.empty((n_filas, n_data_cols + 1), dtype=object)
        for i in range(n_filas):
            tabla_completa[i, 0] = col_base[i]
            for j in range(n_data_cols):
                tabla_completa[i, j + 1] = T[i, j]

        return {
            "fase"       : fase,
            "tabla"      : tabla_completa,
            "fila_pivote": fila_pivote,
            "col_pivote" : col_pivote,
            "mensaje"    : mensaje,
        }

    def _respuesta(
        self,
        estado: str,
        iteraciones: list[dict],
        tableau_final: Tableau | None,
    ) -> dict:
        n = self._n_vars
        m = self._n_restricciones

        z_optimo: Fraction | None = None
        variables_decision: list[Fraction] | None = None
        variables_base: list[str] = []
        nombres = self._nombres_f2 if self._nombres_f2 else self._nombres_f1

        if estado == "optimo" and tableau_final is not None:
            z_raw = tableau_final[0, -1]
            z_optimo = z_raw if self._es_max else -z_raw

            variables_decision = []
            for j in range(n):
                if j in self._base:
                    idx = self._base.index(j)
                    variables_decision.append(tableau_final[idx + 1, -1])
                else:
                    variables_decision.append(Fraction(0))

            variables_base = [nombres[self._base[i]] for i in range(m)]

        encabezados_f1 = ["Base"] + self._nombres_f1
        encabezados_f2 = (["Base"] + self._nombres_f2) if self._nombres_f2 else []

        return {
            "estado"             : estado,
            "z_optimo"           : z_optimo,
            "variables_decision" : variables_decision,
            "encabezados_f1"     : encabezados_f1,
            "encabezados_f2"     : encabezados_f2,
            "variables_base"     : variables_base,
            "iteraciones"        : iteraciones,
        }
