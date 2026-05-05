from src.models.simplex import SolucionadorSimplex

# ---------------------------------------------------------------------------
# Punto de entrada de prueba
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint

    # ------------------------------------------------------------------
    # Caso clásico de maximización — 2 variables, 3 restricciones
    #
    #   MAX  Z = 3X1 + 5X2
    #   s.a. X1        <= 4
    #              2X2 <= 12
    #        3X1 + 5X2 <= 30   (restricción adicional para mayor interés)
    #        X1, X2 >= 0
    #
    # Solución esperada: X1=0, X2=6, Z=30  (sin la 3ª restricción)
    # Con la 3ª restricción: X1=0, X2=6, Z=30 también (verificar)
    # ------------------------------------------------------------------

    datos = {
        "tipo": "MAX",
        "objetivo": [3, 5],
        "restricciones": [
            {"coeficientes": [1, 0], "signo": "<=", "rhs": 4},
            {"coeficientes": [0, 2], "signo": "<=", "rhs": 12},
            {"coeficientes": [3, 5], "signo": "<=", "rhs": 30},
        ],
    }

    solver = SolucionadorSimplex()
    resultado = solver.resolver(datos)

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
            valores  = "".join(f"{str(v):>10}" for v in fila)
            print(etiqueta + valores)

    # ------------------------------------------------------------------
    # Caso de minimización
    #
    #   MIN  Z = 2X1 - 3X2
    #   s.a.      X1 + X2 <= 5
    #   s.a.      -2X1 + X2 <= 2
    #        X1, X2 >= 0
    #
    # Solución esperada: X1=0, X2=0, Z=0
    # (mínimo trivial con no negatividad)
    # ------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("  PRUEBA MINIMIZACIÓN")
    print("=" * 70)

    datos_min = {
        "tipo": "MIN",
        "objetivo": [2, -3],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": "<=", "rhs": 5},
            {"coeficientes": [-2, 1], "signo": "<=", "rhs": 2},
        ],
    }

    resultado_min = solver.resolver(datos_min)
    print("=" * 70)
    print(f"  ESTADO   : {resultado_min['estado']}")
    print(f"  Z ÓPTIMO : {resultado_min['z_optimo']}")
    print(f"  VARIABLES: {resultado_min['variables_decision']}")
    print(f"  BASE FINAL: {resultado_min['variables_base']}")
    print()
    print(f"  ENCABEZADOS DE COLUMNAS PARA LA VISTA:")
    print(f"  {resultado_min['encabezados']}")
    print("=" * 70)

    for idx, it in enumerate(resultado_min["iteraciones"]):
        print(f"\n--- Iteración {idx} ---")
        print(f"  Mensaje     : {it['mensaje']}")
        print(f"  Fila pivote : {it['fila_pivote']}")
        print(f"  Col pivote  : {it['col_pivote']}")
        print(f"  Tableau:")
        tabla = it["tabla"]
        # Imprimir encabezados
        enc = resultado_min["encabezados"]
        header = f"  {'':>6}" + "".join(f"{h:>10}" for h in enc)
        print(header)
        for i, fila in enumerate(tabla):
            etiqueta = f"  F{i:<4}"
            valores = "".join(f"{str(v):>10}" for v in fila)
            print(etiqueta + valores)

    # ------------------------------------------------------------------
    # Caso que requiere otro método (restricción >=)
    # ------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("  PRUEBA RESTRICCIÓN NO SOPORTADA (>=)")
    print("=" * 70)

    datos_invalido = {
        "tipo": "MAX",
        "objetivo": [1, 1],
        "restricciones": [
            {"coeficientes": [1, 1], "signo": ">=", "rhs": 5},
        ],
    }

    resultado_invalido = solver.resolver(datos_invalido)
    print(f"  ESTADO: {resultado_invalido['estado']}")
