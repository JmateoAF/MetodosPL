# Resumen Ejecutivo: Entrada/Salida de Métodos

Fecha: 2026-05-14

## Referencia rápida de formatos

Este documento proporciona ejemplos completos de entrada y salida para cada método.

---

## Estructura de entrada estándar (Problema)

### Ejemplo 1: Problema simple con solo ≤

```python
problema = {
    "tipo": "MAX",                          # Maximización
    "objetivo": [3, 2],                     # MAX 3X1 + 2X2
    "restricciones": [
        {
            "coeficientes": [1, 2],         # Restricción 1: 1X1 + 2X2 <= 10
            "signo": "<=",
            "rhs": 10
        },
        {
            "coeficientes": [2, 1],         # Restricción 2: 2X1 + 1X2 <= 15
            "signo": "<=",
            "rhs": 15
        }
    ]
}
```

### Ejemplo 2: Problema mixto con ≥ y ==

```python
problema = {
    "tipo": "MIN",                          # Minimización
    "objetivo": [2, 3, -1],                 # MIN 2X1 + 3X2 - X3
    "restricciones": [
        {
            "coeficientes": [1, 1, 0],      # 1X1 + 1X2 >= 5
            "signo": ">=",
            "rhs": 5
        },
        {
            "coeficientes": [2, 1, 1],      # 2X1 + 1X2 + 1X3 == 10
            "signo": "==",
            "rhs": 10
        },
        {
            "coeficientes": [1, 2, 2],      # 1X1 + 2X2 + 2X3 <= 20
            "signo": "<=",
            "rhs": 20
        }
    ]
}
```

---

## Salidas por solver

### ResolutorGeneral (opción=1)

#### Entrada
```python
# Usa el ejemplo 1 o 2 arriba
```

#### Salida éxito (estado=0)
```python
{
    "estado": 0,
    "mensaje": "Optimización exitosa.",
    "valor_z": 25.5,                        # Valor óptimo
    "variables": [6.0, 3.5, 0.0]           # [X1=6.0, X2=3.5, X3=0.0]
}
```

#### Salida error (estado ≠ 0)
```python
{
    "estado": 2,                            # 2 = inviable
    "mensaje": "El problema es inviable (sin solución factible).",
    "valor_z": None,
    "variables": None
}
```

#### Códigos de estado
```python
0:  "Optimización exitosa."
1:  "Se alcanzó el límite de iteraciones sin converger."
2:  "El problema es inviable (sin solución factible)."
3:  "El problema es no acotado."
4:  "Problemas numéricos detectados durante la optimización."
-1: "Error en los datos de entrada: ..."
```

---

### SolucionadorSimplex (opción=2)

#### Entrada (SOLO restricciones ≤)
```python
# Usa el ejemplo 1 (con restricciones <=)
```

#### Salida éxito (estado="optimo")
```python
{
    "estado": "optimo",
    "z_optimo": Fraction(51, 2),            # 25.5 exacto
    "variables_decision": [
        Fraction(6, 1),                     # X1 = 6
        Fraction(7, 2),                     # X2 = 3.5
    ],
    "encabezados": [
        "Base",                             # Columna de variable básica
        "X1", "X2",                         # Variables de decisión
        "S1", "S2",                         # Holguras (Slack)
        "RHS"                               # Right-Hand Side
    ],
    "variables_base": [
        "S1",                               # Variable básica de restricción 1 (final)
        "X2",                               # Variable básica de restricción 2 (final)
    ],
    "iteraciones": [
        {
            "tabla": numpy.array([
                ["Z",    Fraction(-3), Fraction(-2), Fraction(0),  Fraction(0),  Fraction(0)],
                ["S1",   Fraction(1),  Fraction(2),  Fraction(1),  Fraction(0),  Fraction(10)],
                ["S2",   Fraction(2),   Fraction(1),  Fraction(0),  Fraction(1),  Fraction(15)],
            ], dtype=object),
            "fila_pivote": 1,               # Fila 1 es pivote
            "col_pivote": 0,                # Columna X1 entra
            "mensaje": "Entra X1, sale S1."
        },
        {
            "tabla": numpy.array([
                ["Z",    Fraction(0),   Fraction(-1, 2), Fraction(3, 2), Fraction(0),  Fraction(45, 2)],
                ["X1",   Fraction(1),   Fraction(2),     Fraction(1),    Fraction(0),  Fraction(10)],
                ["S2",   Fraction(0),   Fraction(-3),    Fraction(-2),   Fraction(1),  Fraction(-5)],
            ], dtype=object),
            "fila_pivote": 2,
            "col_pivote": 1,
            "mensaje": "Entra X2, sale S2."
        },
        # Más iteraciones...
    ]
}
```

#### Salida error (estado="requiere_otro_metodo"|"iniviable")
```python
# Si el problema tiene >= o ==
{
    "estado": "requiere_otro_metodo"|"iniviable",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados": [],
    "variables_base": [],
    "iteraciones": []
}
```

#### Salida no acotado
```python
{
    "estado": "no_acotado",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados": [...],
    "variables_base": [...],
    "iteraciones": [
        {
            # Última iteración muestra dónde se detectó
            "mensaje": "Problema no acotado: no existe cociente mínimo."
        }
    ]
}
```

---

### SolucionadorGranM (opción=3)

#### Entrada (acepta <=, >=, ==)
```python
# Usa el ejemplo 2 (con restricciones mixtas)
```

#### Salida éxito (estado="optimo")
```python
{
    "estado": "optimo",
    "z_optimo": Fraction(25, 2),            # -12.5 para MIN convertido
    "variables_decision": [
        Fraction(3, 1),
        Fraction(2, 1),
        Fraction(5, 1),
    ],
    "encabezados": [
        "Base",
        "X1", "X2", "X3",                   # Variables de decisión
        "S1", "S2",                         # Holgura/exceso
        "A1",                               # Variable artificial
        "RHS"
    ],
    "variables_base": [
        "A1",                               # Artificial en base (o no, según convergencia)
        "X1",                               # X1 básico
        "X2",                               # X2 básico
    ],
    "iteraciones": [
        # ... lista de iteraciones similarmente a Simplex
    ]
}
```

#### Salida inviable
```python
{
    "estado": "inviable",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados": [...],
    "variables_base": [...],
    "iteraciones": [...]
}
```

---

### SolucionadorDosFases (opción=4)

#### Entrada (acepta <=, >=, ==)
```python
# Usa el ejemplo 2
```

#### Salida éxito (estado="optimo")
```python
{
    "estado": "optimo",
    "z_optimo": Fraction(25, 2),
    "variables_decision": [
        Fraction(3, 1),
        Fraction(2, 1),
        Fraction(5, 1),
    ],
    "encabezados_f1": [
        "Base",
        "X1", "X2", "X3",
        "S1", "S2",                         # Holgura/exceso
        "A1",                               # Variable artificial
        "RHS"
    ],
    "encabezados_f2": [
        "Base",
        "X1", "X2", "X3",
        "S1", "S2",                         # Sin artificiales
        "RHS"
    ],
    "variables_base": ["X1", "X2", "X3"],
    "iteraciones": [
        {
            "fase": 1,
            "tabla": numpy.array([
                ["W", Fraction(0), ...],  # Minimize ΣAi
                # ...
            ], dtype=object),
            "fila_pivote": 1,
            "col_pivote": 0,
            "mensaje": "FASE 1 — Entra X1, sale A1."
        },
        # ... más iteraciones de Fase 1 ...
        {
            "fase": 1,
            "tabla": numpy.array([
                ["W", Fraction(0), Fraction(0), ..., Fraction(0)],  # W = 0 ✓ Factible
                # ...
            ], dtype=object),
            "fila_pivote": None,
            "col_pivote": None,
            "mensaje": "FASE 1 — Óptimo alcanzado (W=0)."
        },
        # Transición a Fase 2
        {
            "fase": 2,
            "tabla": numpy.array([
                ["Z", Fraction(-2), Fraction(-3), Fraction(1), ..., Fraction(0)],
                # ...
            ], dtype=object),
            "fila_pivote": None,
            "col_pivote": None,
            "mensaje": "FASE 2 — Óptimo alcanzado."
        }
    ]
}
```

#### Salida inviable (Fase 1 falla)
```python
{
    "estado": "inviable",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados_f1": [...],
    "encabezados_f2": [],                  # No hay Fase 2
    "variables_base": [],
    "iteraciones": [
        # Solo iteraciones de Fase 1
        {
            "fase": 1,
            "tabla": ...,
            "mensaje": "FASE 1 — W > 0. Problema inviable."
        }
    ]
}
```

---

## Formato de tabla (dentro de iteraciones)

La tabla es una matriz numpy con dtype=object (para alojar Fraction).

### Estructura

```
   Columna:  0      1      2      3      4      5      6
Fila 0  ["Z",    -3     -2      0      0      0      0  ]  ← Función objetivo
Fila 1  ["S1",    1      2      1      0      10     ]  ← Restricción 1 (Base="S1")
Fila 2  ["S2",    2      1      0      1      15     ]  ← Restricción 2 (Base="S2")
```

Decodificación:
- `tabla[0, 0]` = "Z" (etiqueta)
- `tabla[0, 1:]` = Coeficientes de Z respecto a X1, X2, S1, S2, RHS
- `tabla[1, 0]` = "S1" (variable básica de la restricción 1)
- `tabla[1, 1:]` = Coeficientes de restricción 1

---

## Mapeo de cambios comunes

### Elemento de entrada a salida

```
Entrada: "tipo": "MAX"         →  Salida: variables en base + Z_opt positivo
         "tipo": "MIN"         →  Salida: variables en base + Z_opt negativo (si interno es -MAX)

Entrada: restricciones <=      →  Salida (Simplex): "optimo" (si converge)
Entrada: restricciones >=,==   →  Salida (Simplex): "requiere_otro_metodo"

Entrada: restricciones mixtas  →  Salida (GranM/DosFases): "optimo"|"inviable"|"no_acotado"
```

---

## Casos de uso: ¿Cuál es el flujo en la UI?

### Flow 1: Usuario ve "Solución Rápida"

```python
VistaGeneral
  ↓
  problema = get_problema_activo() o controlador.problema_activo
  ↓
  resultado = controlador.resolver_LP(problema, 1)  # opción=1 → ResolutorGeneral
  ↓
  # resultado tiene estructura:
  # {estado: 0, mensaje: str, valor_z: float, variables: list[float]}
  ↓
  if resultado["estado"] == 0:
      mostrar "Z óptimo: {valor_z}"
      mostrar "Variables: X1={variables[0]}, X2={variables[1]}, ..."
  else:
      mostrar resultado["mensaje"]
```

### Flow 2: Usuario ve "Simplex" (tabla iterativa)

```python
VistaMatricial(opcion_resolucion=2)  # opción=2 → SolucionadorSimplex
  ↓
  problema = get_problema_activo()
  ↓
  resultado = controlador.resolver_LP(problema, 2)
  ↓
  # resultado tiene estructura:
  # {estado: str, z_optimo: Fraction, iteraciones: list[dict]}
  ↓
  if resultado["estado"] == "requiere_otro_metodo":
      mostrar "Este problema requiere >= o ==. Use Dos Fases o M Grande."
  else:
      for iteracion in resultado["iteraciones"]:
          mostrar tabla con encabezados
          mostrar nombre de variables básicas
          mostrar mensaje ("Entra X1, sale S1")
```

### Flow 3: Usuario ve "M Grande" (tabla iterativa)

```python
VistaMatricial(opcion_resolucion=3)  # opción=3 → SolucionadorGranM
  ↓
  resultado = controlador.resolver_LP(problema, 3)
  ↓
  # Misma estructura que Simplex but sin restricción de signos
  ↓
  if resultado["estado"] == "inviable":
      mostrar "El problema no tiene solución factible"
  else:
      renderizar iteraciones
```

---

## Tabla de conversión: Términos

| Término en código | Término matemático | Ejemplo |
|---|---|---|
| `objetivo` | Función objetivo Z | `[3, 2]` = 3X1 + 2X2 |
| `coeficientes` | Coeficientes de restricción | `[1, 2]` = 1X1 + 2X2 |
| `signo` | Operador de restricción | "<=", ">=", "==" |
| `rhs` | Right-hand side (b_i) | 10 (lado derecho de a·x ≤ 10) |
| `tipo` | Tipo de optimización | "MAX" o "MIN" |
| `z_optimo` / `valor_z` | Z* óptimo | 25.5 o Fraction(51,2) |
| `variables_decision` / `variables` | Valores x* óptimos | [6.0, 3.5] o [Fraction(6,1), ...] |
| `encabezados` | Nombres de columnas | ["Base", "X1", "X2", "S1", "RHS"] |
| `variables_base` | Variables básicas finales | ["X1", "S2"] |
| `iteraciones` | Historial de tableaus | list[dict con tabla, mensaje] |
| `fila_pivote` / `col_pivote` | Elemento pivotante | Índices para marcar el cambio |

---

## Anexo: Función helper para parsear resultado

```python
def interpretar_resultado(resultado, solver_name):
    """Helper para entender el resultado de cualquier solver"""
    
    if resultado is None:
        print(f"{solver_name}: retornó None")
        return
    
    estado = resultado.get("estado")
    
    # ResolutorGeneral (estado int)
    if isinstance(estado, int):
        print(f"{solver_name}: {estado} ({resultado.get('mensaje')})")
        if estado == 0:
            print(f"  Z = {resultado['valor_z']}")
            print(f"  X = {resultado['variables']}")
    
    # SolucionadorSimplex/GranM/DosFases (estado str)
    elif isinstance(estado, str):
        print(f"{solver_name}: {estado}")
        if "encabezados_f1" in resultado:
            print(f"  Fase 1: {len([i for i in resultado['iteraciones'] if i.get('fase')==1])} iteraciones")
            print(f"  Fase 2: {len([i for i in resultado['iteraciones'] if i.get('fase')==2])} iteraciones")
        else:
            print(f"  Iteraciones: {len(resultado.get('iteraciones', []))}")
        
        if estado == "optimo":
            z = resultado.get('z_optimo')
            print(f"  Z = {z} ({float(z) if hasattr(z, '__float__') else z})")
            print(f"  Variables base: {resultado.get('variables_base', [])}")
```

---

Fin del documento.

