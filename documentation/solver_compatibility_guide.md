# Tabla de Compatibilidad: Solvers y Restricciones

Fecha: 2026-05-14

## Quick Reference: Matriz de soporte

| Característica | ResolutorGeneral |      Simplex       | GranM | DosFases |
|---|:---:|:------------------:|:---:|:---:|
| **Método subyacente** | scipy linprog | Tabular (Fraction) | Tabular (Fraction) | Two-Phase (Fraction) |
| **Restricción ≤** | ✓ |         ✓          | ✓ | ✓ |
| **Restricción ≥** | ✓* |         ✗          | ✓ | ✓ |
| **Restricción ==** | ✓ |         ✗          | ✓ | ✓ |
| **MAX/MIN** | ✓ |         ✓          | ✓ | ✓ |
| **Números exactos (Fraction)** | ✗ (float) |         ✓          | ✓ | ✓ |
| **Iteraciones disponibles** | ✗ (¡rápido!) |         ✓          | ✓ | ✓ |
| **Velocidad** | Rápido |       Lento        | Lento | Lento |
| **Detecta inviable** | ✓ |           ✓         | ✓ | ✓ |
| **Detecta no acotado** | ✓ |         ✓          | ✓ | ✓ |

*   **ResolutorGeneral**: transforma interiormente >= en <= multiplicando por -1  
**  SolucionadorSimplex declara "requiere_otro_metodo" si hay >= o ==

---

## Decisión: ¿Qué solver usar?

### Selección según tipo de problema

```
¿Problema con SOLO restricciones ≤?
  ├─ SÍ
  │   └─ ¿Necesito ver cada iteración paso a paso?
  │       ├─ SÍ → USA SIMPLEX (SolucionadorSimplex)
  │       └─ NO  → USA MÉTODO GENERAL (ResolutorGeneral) — más rápido
  │
  └─ NO (hay >= o ==)
      └─ ¿Necesito exactitud decimal completa (Fraction)?
          ├─ SÍ → ELIGE:
          │   ├─ M Grande (SolucionadorGranM) si prefieres penalización
          │   └─ Dos Fases (SolucionadorDosFases) si prefieres limpiar variables artificiales
          │
          └─ NO → USA MÉTODO GENERAL (ResolutorGeneral)
```

### Tabla de decisión (decision tree)

| Problema | Restricciones | Exactitud | Iteraciones necesarias? | Recomendación |
|---|---|---|---|---|
| Simple | ≤ | float ok | No | **ResolutorGeneral** |
| Simple | ≤ | float ok | Sí | **Simplex** |
| Simple | ≤ | Exacta (Fraction) | Sí | **Simplex** |
| Mixto | ≤, ≥, == | float ok | No | **ResolutorGeneral** |
| Mixto | ≤, ≥, == | Exacta | Sí | **GranM o DosFases** |
| Educativa | ≤ | Exacta | Sí (mostrar paso a paso) | **Simplex** |
| Educativa | Mixto | Exacta | Sí (ambas fases) | **DosFases** |

---

## Formato entrada por solver

### ResolutorGeneral (opción=1)

**Acepta:**
```python
{
    "tipo": "MAX"|"MIN",
    "objetivo": [num, num, ...],
    "restricciones": [
        {"coeficientes": [...], "signo": "<="  , "rhs": num},
        {"coeficientes": [...], "signo": ">=" , "rhs": num},  # Transformado internamente
        {"coeficientes": [...], "signo": "==", "rhs": num},
    ]
}
```

**Decisión:** Internamente, transforma:
- `a1·x1 + a2·x2 >= b` → `-a1·x1 - a2·x2 <= -b`
- `==` se mantiene como igualdad en scipy

**Devuelve:** dict con `estado` (int), `valor_z` (float), `variables` (list[float])

---

### SolucionadorSimplex (opción=2)

**Acepta:**
```python
{
    "tipo": "MAX"|"MIN",
    "objetivo": [num, num, ...],
    "restricciones": [
        {"coeficientes": [...], "signo": "<=", "rhs": num},
        {"coeficientes": [...], "signo": "<=", "rhs": num},
        # ...
    ]
}
```

**Rechaza:** `>=` y `==` mediante retorno `{"estado": "requiere_otro_metodo", ...}`

**Devuelve:** dict con `estado` (str: "optimo"|"no_acotado"|"requiere_otro_metodo"|"inviable"), 
`z_optimo` (Fraction), `iteraciones` (list[dict con tabla numpy])

---

### SolucionadorGranM (opción=3)

**Acepta:**
```python
{
    "tipo": "MAX"|"MIN",
    "objetivo": [num, num, ...],
    "restricciones": [
        {"coeficientes": [...], "signo": "<=", "rhs": num},
        {"coeficientes": [...], "signo": ">=", "rhs": num},
        {"coeficientes": [...], "signo": "==", "rhs": num},
        # Cualquier combinación
    ]
}
```

**Procesamiento interno:**
- Introduce variables artificiales con penalización M = 10^9 en la función objetivo
- Utiliza algebraización (resta filas) para limpiar la fila Z inicial
- Si variable artificial queda en base con RHS > 0 → declara inviable

**Devuelve:** dict con `estado` (str: "optimo"|"inviable"|"no_acotado"), 
`z_optimo` (Fraction), `iteraciones` (list[dict])

---

### SolucionadorDosFases (opción=4)

**Acepta:**
```python
{
    "tipo": "MAX"|"MIN",
    "objetivo": [num, num, ...],
    "restricciones": [
        {"coeficientes": [...], "signo": "<=", "rhs": num},
        {"coeficientes": [...], "signo": ">=", "rhs": num},
        {"coeficientes": [...], "signo": "==", "rhs": num},
    ]
}
```

**Procesamiento interno:**
- **Fase 1:** Minimiza W = ΣAi (suma de artificiales). Si W > 0 al terminar → inviable.
- **Fase 2:** Sustituye W por Z objetivo original, elimina columnas de artificiales, continúa Simplex.
- Retorna iteraciones con `"fase": 1 | 2` para cada tabla.

**Devuelve:** dict con `estado` (str), `encabezados_f1` (Fase 1) y `encabezados_f2` (Fase 2),
`iteraciones` (list[dict con fase indicada])

---

## Casos de uso típicos

### Caso 1: Usuario ingresa problema simple con ≤
```
Problema: MAX 3X1 + 2X2
          X1 + X2 <= 10
          2X1 + X2 <= 15
          X1, X2 >= 0
          
UI Flow:
  VistaGeneral.refresh() 
    → Controlador.resolver_LP(problema, 1)  [método general = fast]
    
  VistaMatricial.refresh() 
    → Controlador.resolver_LP(problema, 2)  [simplex = detallado]
```

### Caso 2: Usuario ingresa problema con ≥ y ==
```
Problema: MAX 3X1 + 2X2
          X1 + X2 >= 5         ← ¡Mayor o igual!
          2X1 + X2 == 15       ← ¡Igualdad!
          X1, X2 >= 0

UI Flow:
  VistaGeneral.refresh() 
    → Controlador.resolver_LP(problema, 1)  [ResolutorGeneral maneja internamente]
    
  VistaMatricial (opción=2) 
    → Controlador.resolver_LP(problema, 2)  [Simplex rechaza → "requiere_otro_metodo"]
    
  VistaMatricial (opción=3) 
    → Controlador.resolver_LP(problema, 3)  [GranM ✓]
    
  VistaMatricial (opción=4) 
    → Controlador.resolver_LP(problema, 4)  [DosFases ✓]
```

---

## Mapa de opciones en NavigationApp

```
NavigationApp._create_view() match index:
  case 2:
    return VistaGeneral(controlador)
      → resolver_LP(problema, 1)  [ResolutorGeneral]
  
  case 3:
    return VistaGrafica(controlador)
      → resolver_LP(problema, 1)  [ResolutorGeneral — para el gráfico]
  
  case 4:
    return VistaMatricial(..., opcion_resolucion=2, titulo="Simplex")
      → resolver_LP(problema, 2)  [SolucionadorSimplex]
  
  case 5:
    return VistaMatricial(..., opcion_resolucion=3, titulo="M Grande")
      → resolver_LP(problema, 3)  [SolucionadorGranM]
  
  case 6:
    return VistaMatricial(..., opcion_resolucion=4, titulo="Dos Fases")
      → resolver_LP(problema, 4)  [SolucionadorDosFases]
```

---

## Guía de depuración y errores comunes

| Error | Causa | Solución |
|---|---|---|
| Simplex devuelve "requiere_otro_metodo" | Hay restricción `>=` o `==` | Usar DosFases o GranM |
| GranM declara inviable pero el problema parece factible | Artificiales en base con RHS > 0 | Verificar que todas restricciones se cumplan |
| Resultados Fraction vs float diferentes | Aritmética exacta vs flotante | Esperado; Fraction es exacto |
| `valor_z` vs `z_optimo` en diccionarios | Nombres inconsistentes entre solvers | Usar `valor_z` para ResolutorGeneral, `z_optimo` para tabulares |
| Iteraciones vacías | Solver no tabular (ResolutorGeneral) | Use Simplex/GranM/DosFases |

---

## Notas técnicas avanzadas

### Reinicio de estado en Controlador
```python
class Controlador:
    _solver_casos_general = ResolutorGeneral()    # ← Singleton a nivel de CLASE
    _solver_simplex = SolucionadorSimplex()       # Compartido entre todas las instancias
    _solver_M_grande = SolucionadorGranM()
    _solver_dos_fases = SolucionadorDosFases()
```
**Implicación:** Cada llamada a `resolver()` reinicia el estado interno del solver.

### Orden de columnas en tableau
```
[X1 .. Xn | S1 .. Sm | A1 .. Ap | RHS]
 ↑         ↑         ↑         ↑
 vars      holguras  artificiales  lado derecho
 decis.
```
**En los encabezados:** `["Base", "X1", ..., "Xn", "S1", ..., "RHS"]`

### Elementos de una fila pivote
- Fila 0: Función objetivo (Z o W)
- Filas 1…m: Restricciones (m=número de restricciones)

---

Fin del documento.

