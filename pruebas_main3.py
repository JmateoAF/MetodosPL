
# ---------------------------------------------------------------------------
# Bloque de prueba
# ---------------------------------------------------------------------------

from src.models.m_grande import SolucionadorGranM

import numpy as np

if __name__ == "__main__":
    from pprint import pformat

    def imprimir_tableau(tabla: np.ndarray, encabezados: list[str]) -> None:
        """Imprime el tableau de forma alineada en consola."""
        ancho = 14
        header = f"  {'':>6}" + "".join(f"{h:>{ancho}}" for h in encabezados)
        print(header)
        for i, fila in enumerate(tabla):
            etiqueta = f"  F{i:<5}"
            valores  = "".join(f"{str(v):>{ancho}}" for v in fila)
            print(etiqueta + valores)

    # ══════════════════════════════════════════════════════════════════
    #  PRUEBA 1: MAX con restricciones <=, >= y ==
    #
    #  MAX  Z = 3X1 + 5X2
    #  s.a.
    #       X1        <=  4
    #             2X2 >= 12
    #       3X1 + 2X2 == 18
    #       X1, X2 >= 0
    #
    #  Solución esperada: X1=0, X2=9, Z=45
    # ══════════════════════════════════════════════════════════════════
    datos_max = {
        "tipo": "MAX",
        "objetivo": [3, 5],
        "restricciones": [
            {"coeficientes": [1, 0], "signo": "<=", "rhs": 4},
            {"coeficientes": [0, 2], "signo": ">=", "rhs": 12},
            {"coeficientes": [3, 2], "signo": "==", "rhs": 18},
        ],
    }

    solver = SolucionadorGranM()
    r = solver.resolver(datos_max)

    print("=" * 80)
    print("  PRUEBA 1 — MAX con <=, >= y ==")
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
        imprimir_tableau(it["tabla"], r["encabezados"])
        print()

    # ══════════════════════════════════════════════════════════════════
    #  PRUEBA 2: MIN con restricciones >=
    #
    #  MIN  Z = 2X1 + 3X2
    #  s.a.
    #       X1 + X2 >= 4
    #       X1      >= 2
    #       X1, X2 >= 0
    #
    #  Solución esperada: X1=4, X2=0, Z=8
    # ══════════════════════════════════════════════════════════════════
    datos_min = {
        "tipo": "MIN",
        "objetivo": [2, 3],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": ">=", "rhs": 4},
            {"coeficientes": [1, 0], "signo": ">=", "rhs": 2},
        ],
    }

    solver2 = SolucionadorGranM()
    r2 = solver2.resolver(datos_min)

    print("=" * 80)
    print("  PRUEBA 2 — MIN con >= ")
    print("=" * 80)
    print(f"  Estado            : {r2['estado']}")
    print(f"  Z óptimo          : {r2['z_optimo']}   (esperado: 8)")
    print(f"  Variables decisión: {r2['variables_decision']}   (esperado: X1=4, X2=0)")
    print(f"  Encabezados Vista : {r2['encabezados']}")
    print(f"  Base final        : {r2['variables_base']}")
    print()

    for idx, it in enumerate(r2["iteraciones"]):
        print(f"--- Iteración {idx}: {it['mensaje']}")
        print(f"    fila_pivote={it['fila_pivote']}   col_pivote={it['col_pivote']}")
        imprimir_tableau(it["tabla"], r2["encabezados"])
        print()
    print()

    # ══════════════════════════════════════════════════════════════════
    #  PRUEBA 3: Problema inviable
    #
    #  MAX  Z = X1 + X2
    #  s.a.
    #       X1 + X2 <= 4
    #       X1 + X2 >= 6    ← contradice la anterior
    # ══════════════════════════════════════════════════════════════════
    datos_inv = {
        "tipo": "MAX",
        "objetivo": [1, 1],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": "<=", "rhs": 4},
            {"coeficientes": [1, 1], "signo": ">=", "rhs": 6},
        ],
    }

    solver3 = SolucionadorGranM()
    r3 = solver3.resolver(datos_inv)

    print("=" * 80)
    print("  PRUEBA 3 — Inviable")
    print("=" * 80)
    print(f"  Estado: {r3['estado']}   (esperado: inviable)")
