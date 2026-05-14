"""
simplex.py
==========
Módulo de backend para la resolución paso a paso de problemas de
Programación Lineal mediante el Método Simplex Tabular Estándar.

Restricciones de diseño:
    - Sin GUI, sin prints, sin scipy.
    - Todo el álgebra se realiza con fractions.Fraction para exactitud.
    - Las matrices NumPy usan dtype=object para alojar Fraction.
    - Pensado para software educativo: expone cada iteración completa.

Orden de columnas en cada tableau:
    [X1 ... Xn | S1 ... Sm | RHS]
    donde n = variables de decisión, m = variables de holgura.

La fila Z siempre es la PRIMERA fila del tableau (índice 0).

Autor: Backend Module — MVC Simplex Optimizer
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Tipos de alias para legibilidad
# ---------------------------------------------------------------------------
Tableau = np.ndarray          # dtype=object, valores Fraction
ListaFrac = list[Fraction]


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class SolucionadorSimplex:
    """
    Implementa el algoritmo Simplex tabular estándar paso a paso.

    Soporta:
        - Problemas de MAX y MIN (vía conversión interna MAX = -MIN).
        - Restricciones únicamente de tipo <= (para >= o == devuelve
            "requiere_otro_metodo").
        - Aritmética exacta con fractions.Fraction.
        - Historial completo de iteraciones para renderizado en la GUI.

    Uso desde el Controlador:
        solver = SolucionadorSimplex()
        resultado = solver.resolver(datos_entrada)
    """

    # Límite de iteraciones para evitar ciclos infinitos
    MAX_ITERACIONES: int = 200

    def __init__(self) -> None:
        # Estado interno, se reinicia en cada llamada a resolver()
        self._n_vars: int = 0           # cantidad de variables de decisión
        self._n_restricciones: int = 0  # cantidad de restricciones (== holguras)
        self._es_max: bool = True        # True si el problema original es MAX
        self._base: list[int] = []       # índices de columna de las vars básicas (una por fila)
        self._nombres_cols: list[str] = []  # encabezados de columnas para la Vista

    # ------------------------------------------------------------------
    # Punto de entrada público
    # ------------------------------------------------------------------

    def resolver(self, datos_entrada: dict) -> dict:
        """
        Resuelve el problema de PL y devuelve el historial completo.

        Parámetros
        ----------
        datos_entrada : dict
            {
                "tipo": "MAX" | "MIN",
                "objetivo": [c1, c2, ...],
                "restricciones": [
                    {"coeficientes": [...], "signo": "<=", "rhs": valor},
                    ...
                ]
            }

        Retorna
        -------
        dict con las claves:
            "estado"             : "optimo" | "no_acotado" | "inviable" | "requiere_otro_metodo"
            "z_optimo"           : Fraction | None
            "variables_decision" : list[Fraction] | None
            "encabezados"        : list[str]   ← nombres de columnas para la Vista
            "variables_base"     : list[str]   ← variable básica de cada fila (sin fila Z)
            "iteraciones"        : list[dict]  ← una entrada por tableau generado
        """
        # --- Reiniciar estado interno ---
        self._n_vars = len(datos_entrada["objetivo"])
        self._n_restricciones = len(datos_entrada["restricciones"])
        self._es_max = datos_entrada["tipo"].upper().strip() == "MAX"

        # --- Validar signos (este módulo solo maneja <=) ---
        for r in datos_entrada["restricciones"]:
            if r["signo"].strip() != "<=":
                return self._respuesta_error("requiere_otro_metodo")

        # --- Detectar inviabilidad por RHS negativo ---
        # Con restricciones <= y variables de holgura, la solución básica
        # inicial requiere RHS >= 0 en todas las restricciones.
        # Un RHS negativo hace que la variable de holgura tome valor negativo,
        # lo que viola la no-negatividad y hace el problema inviable.
        for r in datos_entrada["restricciones"]:
            if Fraction(r["rhs"]) < Fraction(0):
                return self._respuesta_error("inviable")

        # --- Construir encabezados de columnas ---
        self._nombres_cols = self._construir_encabezados()

        # --- Construir tableau inicial ---
        tableau = self._construir_tableau(datos_entrada)

        # --- Ejecutar iteraciones Simplex ---
        return self._iterar(tableau)

    # ------------------------------------------------------------------
    # Construcción del tableau
    # ------------------------------------------------------------------

    def _construir_encabezados(self) -> list[str]:
        """
        Genera la lista de nombres de columnas en el orden interno:
            X1 … Xn | S1 … Sm | RHS
        La fila Z no tiene columna propia; es una fila del tableau.
        """
        cols: list[str] = []
        for i in range(1, self._n_vars + 1):
            cols.append(f"X{i}")
        for j in range(1, self._n_restricciones + 1):
            cols.append(f"S{j}")
        cols.append("RHS")
        return cols

    def _construir_tableau(self, datos: dict) -> Tableau:
        """
        Construye la tabla Simplex inicial incluyendo variables de holgura.

        Estructura (filas):
            Fila 0        : fila Z (coeficientes de la F.O. negados para MAX)
            Fila 1 … m    : restricciones aumentadas con holgura

        Columnas:
            0 … n-1   : variables de decisión
            n … n+m-1 : variables de holgura
            n+m       : RHS

        Para MAX se almacena la fila Z como  -Cj  (los coeficientes negativos)
        porque la condición de optimalidad busca que todos los Cj de la fila Z
        sean >= 0.
        """
        n = self._n_vars
        m = self._n_restricciones
        total_cols = n + m + 1          # vars decisión + holguras + RHS
        total_filas = m + 1             # restricciones + fila Z

        # Inicializar con Fraction(0)
        T: Tableau = np.full(
            (total_filas, total_cols),
            Fraction(0),
            dtype=object
        )

        # --- Fila Z (fila 0) ---
        # Para MAX: Z - C1*X1 - C2*X2 - ... = 0
        # Se almacena como (-C1, -C2, ..., 0, ..., 0) en la fila 0.
        # Para MIN: convertimos a MAX multiplicando el objetivo por -1,
        # por lo que los coeficientes en la fila Z quedan positivos.
        signo_z = Fraction(1) if self._es_max else Fraction(-1)
        for j, coef in enumerate(datos["objetivo"]):
            T[0, j] = Fraction(-coef) * signo_z

        # --- Filas de restricciones (filas 1 … m) ---
        for i, r in enumerate(datos["restricciones"]):
            fila = i + 1        # desplazamiento: fila 0 es Z
            # Variables de decisión
            for j, coef in enumerate(r["coeficientes"]):
                T[fila, j] = Fraction(coef)
            # Variable de holgura correspondiente (matriz identidad)
            T[fila, n + i] = Fraction(1)
            # RHS
            T[fila, total_cols - 1] = Fraction(r["rhs"])

        # --- Inicializar vector de base (holguras son la base inicial) ---
        # La variable básica de la restricción i es S(i+1), columna n+i.
        # _base[i] corresponde a la fila de restricción i (fila i+1 del tableau).
        self._base = [n + i for i in range(m)]

        return T

    # ------------------------------------------------------------------
    # Algoritmo Simplex (bucle de iteraciones)
    # ------------------------------------------------------------------

    def _iterar(self, tableau: Tableau) -> dict:
        """
        Ejecuta el bucle Simplex hasta alcanzar la solución óptima,
        detectar no acotamiento o agotar el límite de iteraciones.

        Cada iteración registra:
            - Copia del tableau ANTES del pivoteo (tableau actual).
            - Índices de fila y columna pivote.
            - Mensaje descriptivo para la Vista.

        Retorna el diccionario de salida completo.
        """
        iteraciones: list[dict] = []
        m = self._n_restricciones

        for _ in range(self.MAX_ITERACIONES):

            # 1. Verificar optimalidad: todos los coeficientes de Z >= 0
            col_pivote = self._seleccionar_columna_pivote(tableau)
            if col_pivote is None:
                # Condición de optimalidad alcanzada
                iteraciones.append(self._snapshot(tableau, None, None, "Solución óptima encontrada."))
                return self._construir_resultado("optimo", tableau, iteraciones)

            # 2. Prueba del cociente mínimo (identifica la fila pivote)
            fila_pivote = self._seleccionar_fila_pivote(tableau, col_pivote)
            if fila_pivote is None:
                # Ningún cociente válido → problema no acotado
                iteraciones.append(self._snapshot(tableau, None, col_pivote, "Problema no acotado: no existe cociente mínimo."))
                return self._construir_resultado("no_acotado", tableau, iteraciones)

            # 3. Registrar snapshot ANTES del pivoteo
            # fila_pivote es el índice real en el tableau (1…m);
            # el índice en _base es fila_pivote - 1 (sin contar la fila Z).
            var_entra = self._nombres_cols[col_pivote]
            var_sale  = self._nombres_cols[self._base[fila_pivote - 1]]
            mensaje   = f"Entra {var_entra}, sale {var_sale}."
            iteraciones.append(self._snapshot(tableau, fila_pivote, col_pivote, mensaje))

            # 4. Pivotear
            tableau = self._pivotear(tableau, fila_pivote, col_pivote)

            # 5. Actualizar vector de base (índice base = fila_pivote - 1)
            self._base[fila_pivote - 1] = col_pivote

        # Si se agotó el límite, retornar el último estado como no_acotado
        iteraciones.append(self._snapshot(tableau, None, None, "Límite de iteraciones alcanzado."))
        return self._construir_resultado("no_acotado", tableau, iteraciones)

    # ------------------------------------------------------------------
    # Operaciones del tableau
    # ------------------------------------------------------------------

    def _seleccionar_columna_pivote(self, T: Tableau) -> int | None:
        """
        Regla de entrada: columna con el coeficiente MÁS NEGATIVO en la fila Z.
        Si todos son >= 0, el tableau es óptimo (retorna None).
        """
        fila_z = T[0, :-1]    # Fila 0 es Z; excluir columna RHS
        min_val = Fraction(0)
        col_pivote = None

        for j, val in enumerate(fila_z):
            if val < min_val:
                min_val = val
                col_pivote = j

        return col_pivote

    def _seleccionar_fila_pivote(self, T: Tableau, col_pivote: int) -> int | None:
        """
        Prueba del cociente mínimo (Minimum Ratio Test):
            θ = RHS_i / T[i, col_pivote]   solo si T[i, col_pivote] > 0

        Retorna el índice de la fila con el cociente mínimo positivo,
        o None si no existe (problema no acotado).
        """
        m = self._n_restricciones
        min_ratio = None
        fila_pivote = None

        # Las restricciones están en filas 1…m (fila 0 es Z)
        for i in range(1, m + 1):
            elemento = T[i, col_pivote]
            if elemento > Fraction(0):
                ratio = T[i, -1] / elemento
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    fila_pivote = i

        return fila_pivote

    def _pivotear(self, T: Tableau, fila_p: int, col_p: int) -> Tableau:
        """
        Realiza las operaciones de fila para convertir la columna pivote
        en un vector canónico (1 en fila_p, 0 en el resto).

        Toda la aritmética es exacta con Fraction.

        Retorna una NUEVA copia del tableau pivoteado.
        """
        T = T.copy()
        pivote = T[fila_p, col_p]

        # Normalizar fila pivote (dividir por el elemento pivote)
        T[fila_p, :] = [v / pivote for v in T[fila_p, :]]

        # Eliminar el resto de filas (incluida la fila Z)
        for i in range(T.shape[0]):
            if i != fila_p:
                factor = T[i, col_p]
                if factor != Fraction(0):
                    T[i, :] = [T[i, k] - factor * T[fila_p, k] for k in range(T.shape[1])]

        return T

    # ------------------------------------------------------------------
    # Construcción de resultados y snapshots
    # ------------------------------------------------------------------

    def _snapshot(
        self,
        T: Tableau,
        fila_pivote: int | None,
        col_pivote: int | None,
        mensaje: str,
    ) -> dict:
        """
        Captura el estado actual del tableau para el historial de la Vista.

        La tabla exportada incluye una columna extra al inicio: "Base",
        que indica la variable básica de cada fila de restricción,
        y "Z" para la última fila.
        """
        m = self._n_restricciones

        # Columna de base: fila 0 es Z, luego las variables básicas de cada restricción
        col_base: list[Any] = ["Z"]
        col_base += [self._nombres_cols[self._base[i]] for i in range(m)]

        # Construir matriz con columna base antepuesta
        n_filas, n_data_cols = T.shape
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

        Para problemas MIN el valor Z se re-invierte al dominio original
        (se multiplica por -1) antes de devolverlo.
        """
        n = self._n_vars
        m = self._n_restricciones

        z_optimo = None
        variables_decision = None

        if estado == "optimo":
            # Valor Z en la celda [0, RHS] — fila 0 es Z
            z_raw = T[0, -1]
            # Para MIN habíamos multiplicado el objetivo por -1, así que revertimos
            z_optimo = z_raw if self._es_max else -z_raw

            # Extraer valores de variables de decisión desde la base.
            # _base[i] es el índice de columna de la var básica de la restricción i,
            # que ocupa la fila i+1 del tableau.
            variables_decision = []
            for j in range(n):
                if j in self._base:
                    idx_base = self._base.index(j)
                    fila_tableau = idx_base + 1   # +1 porque fila 0 es Z
                    variables_decision.append(T[fila_tableau, -1])
                else:
                    variables_decision.append(Fraction(0))

        # Encabezados para la Vista: "Base" + columnas de datos
        encabezados_vista = ["Base"] + self._nombres_cols

        # Nombres de la variable básica por fila de restricción (sin fila Z)
        variables_base = [self._nombres_cols[self._base[i]] for i in range(m)]

        return {
            "estado"             : estado,
            "z_optimo"           : z_optimo,
            "variables_decision" : variables_decision,
            "encabezados"        : encabezados_vista,   # para la Vista
            "variables_base"     : variables_base,       # base final (sin fila Z)
            "iteraciones"        : iteraciones,
        }

    def _respuesta_error(self, estado: str) -> dict:
        """Devuelve un diccionario de error con estructura completa."""
        return {
            "estado"             : estado,
            "z_optimo"           : None,
            "variables_decision" : None,
            "encabezados"        : [],
            "variables_base"     : [],
            "iteraciones"        : [],
        }