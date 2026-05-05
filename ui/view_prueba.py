import pprint

import numpy as np

from src.controller import controlador
from src.controller.controlador import Controlador

class View:

    def __init__(self, controlador : Controlador):
        self.controlador = controlador

    def prueba_rapida(self):
        self._imprimer_prueba_1()
        self._imprimer_prueba_2()
        self._imprimer_prueba_3()
        self._imprimir_prueba_4()


    def _imprimer_prueba_1(self):
        # Prueba del metodo general
        print("=" * 60)
        print("  CASO GENERAL")
        print("=" * 60)

        datos_prueba_1 = {
            "tipo": "MAX",
            "objetivo": [4, 2, 8],
            "restricciones": [
                {"coeficientes": [2, 1, 0], "signo": ">=", "rhs": 10},
                {"coeficientes": [1, -1, 3], "signo": "<=", "rhs": 15},
                {"coeficientes": [0, 2, 1], "signo": "==", "rhs": 8},
            ],
        }
        resultado_1 = self.controlador.resolver_LP(datos_prueba_1, 1)
        print("Resultado:")
        pprint.pprint(resultado_1)

    def _imprimer_prueba_2(self):
        print("=" * 60)
        print("  METODO SIMPLEX")
        print("=" * 60)
        datos = {
            "tipo": "MAX",
            "objetivo": [3, 5],
            "restricciones": [
                {"coeficientes": [1, 0], "signo": "<=", "rhs": 4},
                {"coeficientes": [0, 2], "signo": "<=", "rhs": 12},
                {"coeficientes": [3, 5], "signo": "<=", "rhs": 30},
            ],
        }

        resultado = self.controlador.resolver_LP(datos, 2)

        print("=" * 70)
        print(f"  ESTADO   : {resultado['estado']}")
        print(f"  Z ÓPTIMO : {resultado['z_optimo']}")
        print(f"  VARIABLES: {resultado['variables_decision']}")
        print(f"  BASE FINAL: {resultado['variables_base']}")
        print()
        print(f"  ENCABEZADOS DE COLUMNAS PARA LA VISTA:")
        print(f"  {resultado['encabezados']}")
        print("=" * 70)

        for idx, it in enumerate(resultado["iteraciones"]):
            print(f"\n--- Iteración {idx} ---")
            print(f"  Mensaje     : {it['mensaje']}")
            print(f"  Fila pivote : {it['fila_pivote']}")
            print(f"  Col pivote  : {it['col_pivote']}")
            print(f"  Tableau:")
            tabla = it["tabla"]
            # Imprimir encabezados
            enc = resultado["encabezados"]
            header = f"  {'':>6}" + "".join(f"{h:>10}" for h in enc)
            print(header)
            for i, fila in enumerate(tabla):
                etiqueta = f"  F{i:<4}"
                valores = "".join(f"{str(v):>10}" for v in fila)
                print(etiqueta + valores)

    def _imprimer_prueba_3(self):
        datos_max = {
            "tipo": "MAX",
            "objetivo": [3, 5],
            "restricciones": [
                {"coeficientes": [1, 0], "signo": "<=", "rhs": 4},
                {"coeficientes": [0, 2], "signo": ">=", "rhs": 12},
                {"coeficientes": [3, 2], "signo": "==", "rhs": 18},
            ],
        }

        r = self.controlador.resolver_LP(datos_max, 3)

        print("=" * 80)
        print("  Metodo de la M grande")
        print("=" * 80)
        print(f"  Estado            : {r['estado']}")
        print(f"  Z óptimo          : {r['z_optimo']}   (esperado: 45)")
        print(f"  Variables decisión: {r['variables_decision']}   (esperado: X1=0, X2=9)")
        print(f"  Encabezados Vista : {r['encabezados']}")
        print(f"  Base final        : {r['variables_base']}")
        print()

        for idx, it in enumerate(r["iteraciones"]):
            print(f"--- Iteración {idx}: {it['mensaje']}")
            print(f"    fila_pivote={it['fila_pivote']}   col_pivote={it['col_pivote']}")
            self._imprimir_tableau(it["tabla"], r["encabezados"])
            print()

    def _imprimir_tableau(self, tabla: np.ndarray, encabezados: list[str]) -> None:
        """Imprime el tableau de forma alineada en consola."""
        ancho = 14
        header = f"  {'':>6}" + "".join(f"{h:>{ancho}}" for h in encabezados)
        print(header)
        for i, fila in enumerate(tabla):
            etiqueta = f"  F{i:<5}"
            valores = "".join(f"{str(v):>{ancho}}" for v in fila)
            print(etiqueta + valores)

    def _imprimir_prueba_4(self):
        datos_1 = {
            "tipo": "MAX",
            "objetivo": [3, 5],
            "restricciones": [
                {"coeficientes": [1, 0], "signo": "<=", "rhs": 4},
                {"coeficientes": [0, 2], "signo": ">=", "rhs": 12},
                {"coeficientes": [3, 2], "signo": "==", "rhs": 18},
            ],
        }

        r1 = self.controlador.resolver_LP(datos_1, 4)

        print("=" * 75)
        print("  Metodo de dos fases")
        print("=" * 75)
        print(f"  Estado            : {r1['estado']}")
        print(f"  Z óptimo          : {r1['z_optimo']}   (esperado: 45)")
        print(f"  Variables decisión: {r1['variables_decision']}   (esperado: X1=0, X2=9)")
        print(f"  Base final        : {r1['variables_base']}")
        print()

        enc_actual = r1["encabezados_f1"]
        for idx, it in enumerate(r1["iteraciones"]):
            enc = r1["encabezados_f1"] if it["fase"] == 1 else r1["encabezados_f2"]
            print(f"--- [{it['mensaje']}]")
            print(f"    fila_pivote={it['fila_pivote']}  col_pivote={it['col_pivote']}")
            self._imprimir_tableau_2(it["tabla"], enc)
            print()

    def _imprimir_tableau_2(self, tabla: np.ndarray, encabezados: list[str]) -> None:
        ancho = 12
        print("  " + "".join(f"{h:>{ancho}}" for h in encabezados))
        for i, fila in enumerate(tabla):
            print(f"F{i:<2}" + "".join(f"{str(v):>{ancho}}" for v in fila))