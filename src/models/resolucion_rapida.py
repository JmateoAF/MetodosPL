"""
resolucion_rapida.py
====================
Módulo de backend para la resolución eficiente de problemas de Programación
Lineal (PL) usando el "Método General" basado en scipy.optimize.linprog.

Responsabilidades:
    - Transformar el diccionario de entrada del Controlador al formato
        que exige linprog (minimización, restricciones separadas, etc.).
    - Devolver un diccionario de resultados estructurado y limpio.

Sin dependencias de interfaz gráfica (PyQt6 u otras).
Autor: Backend Module — MVC Linear Optimizer
"""

import numpy as np
from scipy.optimize import linprog


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------

class ResolutorGeneral:
    """
    Encapsula la lógica de transformación y resolución de un problema de
    Programación Lineal mediante scipy.optimize.linprog.

    Uso típico (desde el Controlador):
        resolutor = ResolutorGeneral(datos_entrada)
        resultado = resolutor.resolver()

    También puede usarse la función de conveniencia de módulo:
        resultado = resolver_caso_general(datos_entrada)
    """

    # Mapa de códigos de estado de linprog a descripciones legibles
    _MENSAJES_ESTADO = {
        0: "Optimización exitosa.",
        1: "Se alcanzó el límite de iteraciones sin converger.",
        2: "El problema es inviable (sin solución factible).",
        3: "El problema es no acotado.",
        4: "Problemas numéricos detectados durante la optimización.",
    }

    def __init__(self, datos_entrada: dict):
        """
        Inicializa el resolutor con los datos crudos del Controlador.

        Parámetros
        ----------
        datos_entrada : dict
            Diccionario con las claves:
                "tipo"          : "MAX" o "MIN"
                "objetivo"      : lista de coeficientes de Z
                "restricciones" : lista de dicts con "coeficientes",
                                "signo" y "rhs"
        """
        self._datos = datos_entrada

        # Resultados internos (se llenan tras llamar a resolver())
        self._c: np.ndarray = None          # coeficientes objetivo para linprog
        self._A_ub: list = []               # filas de restricciones <=
        self._b_ub: list = []               # RHS de restricciones <=
        self._A_eq: list = []               # filas de restricciones ==
        self._b_eq: list = []               # RHS de restricciones ==
        self._es_max: bool = False          # True si el problema original es MAX

    # ------------------------------------------------------------------
    # Métodos privados de preparación
    # ------------------------------------------------------------------

    def _preparar_objetivo(self) -> None:
        """
        Convierte los coeficientes de la función objetivo a float64.
        Si el problema es de maximización, invierte los signos porque
        linprog **minimiza** por defecto:
            max Z(x) ≡ min -Z(x)
        """
        tipo = self._datos.get("tipo", "MIN").upper().strip()
        self._es_max = (tipo == "MAX")

        c = np.array(self._datos["objetivo"], dtype=np.float64)

        if self._es_max:
            c = -c  # Inversión de signo para convertir MAX → MIN

        self._c = c

    def _preparar_restricciones(self) -> None:
        """
        Separa la lista de restricciones en las matrices A_ub/b_ub (≤)
        y A_eq/b_eq (==) que espera linprog.

        Reglas de transformación de signos:
            <=  →  se agrega directamente a A_ub / b_ub
            >=  →  se multiplica toda la fila por -1 (invierte la
                    desigualdad) y se agrega a A_ub / b_ub
            ==  →  se agrega directamente a A_eq / b_eq
        """
        self._A_ub = []
        self._b_ub = []
        self._A_eq = []
        self._b_eq = []

        for restriccion in self._datos["restricciones"]:
            coefs = np.array(restriccion["coeficientes"], dtype=np.float64)
            rhs   = float(restriccion["rhs"])
            signo = restriccion["signo"].strip()

            if signo == "<=":
                # linprog acepta ≤ de forma nativa
                self._A_ub.append(coefs)
                self._b_ub.append(rhs)

            elif signo == ">=":
                # Multiplicar por -1: ax ≥ b  ⟺  -ax ≤ -b
                self._A_ub.append(-coefs)
                self._b_ub.append(-rhs)

            elif signo == "==":
                self._A_eq.append(coefs)
                self._b_eq.append(rhs)

            else:
                raise ValueError(
                    f"Signo de restricción no reconocido: '{signo}'. "
                    "Use '<=', '>=' o '=='."
                )

    def _construir_matrices(self):
        """
        Convierte las listas internas en arrays de NumPy (o None si están
        vacías), listos para pasarlos a linprog.

        Retorna
        -------
        tuple : (A_ub, b_ub, A_eq, b_eq)
        """
        A_ub = np.array(self._A_ub, dtype=np.float64) if self._A_ub else None
        b_ub = np.array(self._b_ub, dtype=np.float64) if self._b_ub else None
        A_eq = np.array(self._A_eq, dtype=np.float64) if self._A_eq else None
        b_eq = np.array(self._b_eq, dtype=np.float64) if self._b_eq else None
        return A_ub, b_ub, A_eq, b_eq

    def _construir_bounds(self):
        """
        Define los límites de cada variable de decisión.
        Condición estándar de no negatividad: xᵢ ≥ 0 (bound = (0, None)).
        """
        n = len(self._c)
        return [(0.0, None)] * n

    # ------------------------------------------------------------------
    # Método público principal
    # ------------------------------------------------------------------

    def resolver(self) -> dict:
        """
        Ejecuta la resolución completa del problema de PL.

        Pasos:
            1. Prepara el vector objetivo.
            2. Prepara y clasifica las restricciones.
            3. Llama a scipy.optimize.linprog.
            4. Postprocesa el resultado (re-inversión de signo para MAX).
            5. Devuelve el diccionario de salida estandarizado.

        Retorna
        -------
        dict con las claves:
            "estado"    : int   — código de estado (0=óptimo, 2=inviable, 3=no acotado…)
            "mensaje"   : str   — descripción del estado
            "valor_z"   : float | None — valor óptimo de Z (None si no hay solución)
            "variables" : list  | None — valores de las variables [x1, x2, …] (None si no hay solución)
        """
        try:
            # --- 1. Preparación ---
            self._preparar_objetivo()
            self._preparar_restricciones()
            A_ub, b_ub, A_eq, b_eq = self._construir_matrices()
            bounds = self._construir_bounds()

            # --- 2. Llamada a linprog ---
            resultado_scipy = linprog(
                c       = self._c,
                A_ub    = A_ub,
                b_ub    = b_ub,
                A_eq    = A_eq,
                b_eq    = b_eq,
                bounds  = bounds,
                method  = "highs",   # Método HiGHS: robusto y eficiente
            )

            estado  = resultado_scipy.status
            mensaje = self._MENSAJES_ESTADO.get(estado, resultado_scipy.message)

            # --- 3. Postproceso (solo si hay solución óptima) ---
            if estado == 0:
                valor_z = float(resultado_scipy.fun)

                # Si era MAX, re-invertimos el signo del valor objetivo
                if self._es_max:
                    valor_z = -valor_z

                variables = [float(v) for v in resultado_scipy.x]
            else:
                valor_z   = None
                variables = None

            return {
                "estado"    : estado,
                "mensaje"   : mensaje,
                "valor_z"   : valor_z,
                "variables" : variables,
            }

        except ValueError as e:
            # Error de validación en los datos de entrada
            return {
                "estado"    : -1,
                "mensaje"   : f"Error en los datos de entrada: {e}",
                "valor_z"   : None,
                "variables" : None,
            }
        except Exception as e:
            # Error inesperado en tiempo de ejecución
            return {
                "estado"    : -1,
                "mensaje"   : f"Error interno del resolutor: {e}",
                "valor_z"   : None,
                "variables" : None,
            }


# ---------------------------------------------------------------------------
# Función de conveniencia de módulo (interfaz pública para el Controlador)
# ---------------------------------------------------------------------------

def resolver_caso_general(datos_entrada: dict) -> dict:
    """
    Función de conveniencia que instancia ResolutorGeneral y llama a resolver().

    Esta es la función que el Controlador debe importar y llamar.

    Parámetros
    ----------
    datos_entrada : dict
        Diccionario con estructura definida en el contrato de datos de entrada.

    Retorna
    -------
    dict
        Diccionario con estructura definida en el contrato de datos de salida.

    Ejemplo
    -------
    #>>> resultado = resolver_caso_general(datos_entrada)
    #>>> print(resultado["valor_z"])
    """
    resolutor = ResolutorGeneral(datos_entrada)
    return resolutor.resolver()