from src.models.dos_fases import SolucionadorDosFases

import numpy as np
# ---------------------------------------------------------------------------
# Bloque de prueba
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    def imprimir_tableau(tabla: np.ndarray, encabezados: list[str]) -> None:
        ancho = 12
        print("  " + "".join(f"{h:>{ancho}}" for h in encabezados))
        for i, fila in enumerate(tabla):
            print(f"F{i:<2}" + "".join(f"{str(v):>{ancho}}" for v in fila))

    # ══════════════════════════════════════════════════════════════════
    #  PRUEBA 1: MAX con <=, >= y ==
    #
    #  MAX  Z = 3X1 + 5X2
    #  s.a.
    #        X1        <=  4
    #              2X2 >= 12   →  X2 >= 6
    #       3X1 + 2X2  == 18
    #       X1, X2 >= 0
    #
    #  Región factible: X1=0, X2=9  →  Z = 45
    # ══════════════════════════════════════════════════════════════════
    datos_1 = {
        "tipo": "MAX",
        "objetivo": [3, 5],
        "restricciones": [
            {"coeficientes": [1, 0], "signo": "<=", "rhs": 4},
            {"coeficientes": [0, 2], "signo": ">=", "rhs": 12},
            {"coeficientes": [3, 2], "signo": "==", "rhs": 18},
        ],
    }

    solver = SolucionadorDosFases()
    r1 = solver.resolver(datos_1)

    print("=" * 75)
    print("  PRUEBA 1 — MAX con <=, >= y ==")
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
        imprimir_tableau(it["tabla"], enc)
        print()

    # ══════════════════════════════════════════════════════════════════
    #  PRUEBA 2: MIN con >=
    #
    #  MIN  Z = 2X1 + 3X2
    #  s.a.
    #       X1 + X2 >= 4
    #       X1      >= 2
    #       X1, X2 >= 0
    #
    #  Solución: X1=4, X2=0, Z=8
    # ══════════════════════════════════════════════════════════════════
    datos_2 = {
        "tipo": "MIN",
        "objetivo": [2, 3],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": ">=", "rhs": 4},
            {"coeficientes": [1, 0], "signo": ">=", "rhs": 2},
        ],
    }

    solver2 = SolucionadorDosFases()
    r2 = solver2.resolver(datos_2)

    print("=" * 75)
    print("  PRUEBA 2 — MIN con >=")
    print("=" * 75)
    print(f"  Estado            : {r2['estado']}")
    print(f"  Z óptimo          : {r2['z_optimo']}   (esperado: 8)")
    print(f"  Variables decisión: {r2['variables_decision']}   (esperado: X1=4, X2=0)")
    print()

    # ══════════════════════════════════════════════════════════════════
    #  PRUEBA 3: Problema inviable
    #
    #  MAX  Z = X1 + X2
    #  s.a.
    #       X1 + X2 <= 4
    #       X1 + X2 >= 6   ← contradice la anterior
    # ══════════════════════════════════════════════════════════════════
    datos_3 = {
        "tipo": "MAX",
        "objetivo": [1, 1],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": "<=", "rhs": 4},
            {"coeficientes": [1, 1], "signo": ">=", "rhs": 6},
        ],
    }

    solver3 = SolucionadorDosFases()
    r3 = solver3.resolver(datos_3)

    print("=" * 75)
    print("  PRUEBA 3 — Inviable")
    print("=" * 75)
    print(f"  Estado: {r3['estado']}   (esperado: inviable)")
    print(f"  Iteraciones registradas: {len(r3['iteraciones'])}")
    print(f"  Fase de cada iteración : {[it['fase'] for it in r3['iteraciones']]}")