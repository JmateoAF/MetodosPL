
# ---------------------------------------------------------------------------
# Bloque de prueba
# ---------------------------------------------------------------------------

import pprint

from src.models.resolucion_rapida import ResolutorGeneral

if __name__ == "__main__":

    print("=" * 60)
    print("  PRUEBA 1 — Maximización con restricciones mixtas")
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
    resolver_todo = ResolutorGeneral()
    resultado_1 = resolver_todo.resolver(datos_prueba_1)
    print("Resultado:")
    pprint.pprint(resultado_1)

    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  PRUEBA 2 — Minimización clásica")
    print("=" * 60)

    datos_prueba_2 = {
        "tipo": "MIN",
        "objetivo": [1, 2],
        "restricciones": [
            {"coeficientes": [1, 1],  "signo": ">=", "rhs": 4},
            {"coeficientes": [1, -1], "signo": "<=", "rhs": 2},
        ],
    }

    resultado_2 = resolver_todo.resolver(datos_prueba_2)
    print("Resultado:")
    pprint.pprint(resultado_2)

    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  PRUEBA 3 — Problema inviable (sin solución factible)")
    print("=" * 60)

    datos_prueba_3 = {
        "tipo": "MIN",
        "objetivo": [1, 1],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": ">=", "rhs": 10},
            {"coeficientes": [1, 1], "signo": "<=", "rhs": 5},
        ],
    }

    resultado_3 = resolver_todo.resolver(datos_prueba_3)
    print("Resultado:")
    pprint.pprint(resultado_3)
