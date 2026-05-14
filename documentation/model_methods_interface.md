# Interfaz de métodos de modelos
## Especificación de formatos de entrada y salida

Fecha: 2026-05-14

Este documento detalla la interfaz de cada método en la capa de modelos (`src/models/`),
incluyendo la estructura exacta del diccionario esperado como entrada y el formato devuelto.

---

## 1. Controlador (`src/controller/controlador.py`)

### Clase: `Controlador`

#### Método: `resolver_LP(datos_entrada: dict, opcion: int) -> dict | None`

**Propósito:** Orquesta la resolución de un problema de programación lineal según la opción especificada.

**Parámetros:**
- `datos_entrada` (dict): Diccionario del problema con estructura:
  ```python
  {
      "tipo": "MAX" | "MIN",  # string (en mayúsculas)
      "objetivo": [c1, c2, c3, ...],  # list de números (int/float/Fraction)
      "restricciones": [
          {
              "coeficientes": [a1, a2, a3, ...],  # list de números
              "signo": "<=" | ">=" | "==",        # string
              "rhs": valor_float_o_int             # número (lado derecho)
          },
          ...
      ]
  }
  ```
- `opcion` (int): Código del método a usar:
  - `1` → `ResolutorGeneral` (scipy linprog)
  - `2` → `SolucionadorSimplex`
  - `3` → `SolucionadorGranM`
  - `4` → `SolucionadorDosFases`

**Retorna:**
- Si `opcion` está en rango: devuelve el dict devuelto por el solver correspondiente.
- Si `opcion` no reconocida: `None`

**Solvers internos:**
- opción 1 → `self._solver_casos_general.resolver(datos_entrada)`
- opción 2 → `self._solver_simplex.resolver(datos_entrada)`
- opción 3 → `self._solver_M_grande.resolver(datos_entrada)`
- opción 4 → `self._solver_dos_fases.resolver(datos_entrada)`

---

#### Método: `operar_problema(datos_entrada: dict, opcion: int, indice: int = 0) -> dict | None`

**Propósito:** Operar sobre el historial de problemas (guardar, obtener, eliminar).

**Parámetros:**
- `datos_entrada` (dict): El problema completo (misma estructura que `resolver_LP`). 
  Obligatorio para opción 1, puede ser None para otras opciones.
- `opcion` (int):
  - `1` → guardar un problema
  - `2` → obtener un problema por índice
  - `3` → eliminar un problema por índice
- `indice` (int, default 0): Índice en el historial (usado en opciones 2 y 3).

**Retorna:**
- opción 1: devuelve el mismo `datos_entrada` (del método `ingresar_problema`).
- opción 2: devuelve el problema en ese índice (mismo formato que entrada).
- opción 3: devuelve el problema eliminado (antes de ser removido).

---

#### Método: `obtener_historial_de_problema() -> list[dict]`

**Propósito:** Devuelve la lista completa del historial.

**Retorna:**
```python
[
    {
        "tipo": "MAX" | "MIN",
        "objetivo": [...],
        "restricciones": [...]
    },
    ...
]
```

---

## 2. Historial de Problemas (`src/models/historial_de_problemas.py`)

### Clase: `HistorialDeProblemas`

#### Método: `ingresar_problema(datos_entrada: dict) -> dict`

**Propósito:** Guarda un problema en el historial y lo devuelve.

**Entrada:**
```python
{
    "tipo": "MAX" | "MIN",
    "objetivo": [c1, c2, ...],
    "restricciones": [
        {
            "coeficientes": [a1, a2, ...],
            "signo": "<=" | ">=" | "==",
            "rhs": valor
        },
        ...
    ]
}
```

**Salida:** El mismo diccionario (copia o referencia, según implementación).

---

#### Método: `obtener_historial_de_problemas() -> list[dict]`

**Propósito:** Devuelve todos los problemas guardados.

**Entrada:** Ninguna (método sin parámetros).

**Salida:**
```python
[
    {"tipo": "MAX"|"MIN", "objetivo": [...], "restricciones": [...]},
    {"tipo": "MAX"|"MIN", "objetivo": [...], "restricciones": [...]},
    ...
]
```

---

#### Método: `obtener_problemas(indice: int) -> dict`

**Propósito:** Devuelve un problema específico por índice.

**Entrada:** `indice` (int) — índice en el historial.

**Salida:**
```python
{
    "tipo": "MAX" | "MIN",
    "objetivo": [...],
    "restricciones": [...]
}
```

---

#### Método: `eliminar_problema(indice: int) -> dict`

**Propósito:** Elimina y devuelve un problema del historial.

**Entrada:** `indice` (int).

**Salida:** El problema eliminado (estructura idéntica a entrada de `ingresar_problema`).

---

## 3. Resolución Rápida (`src/models/resolucion_rapida.py`)

### Clase: `ResolutorGeneral`

#### Método: `resolver(datos_entrada: dict) -> dict`

**Propósito:** Resuelve el LP mediante `scipy.optimize.linprog` (método "HiGHS").

**Entrada:**
```python
{
    "tipo": "MAX" | "MIN",
    "objetivo": [c1, c2, c3, ...],  # números convertibles a float
    "restricciones": [
        {
            "coeficientes": [a1, a2, ...],
            "signo": "<=" | ">=" | "==",
            "rhs": valor_numérico
        },
        ...
    ]
}
```

**Salida (éxito, estado=0):**
```python
{
    "estado": 0,                              # int: código de estado
    "mensaje": "Optimización exitosa.",       # str: descripción
    "valor_z": float,                         # float | None: valor óptimo de Z
    "variables": [x1, x2, ...],               # list[float] | None: valores X
}
```

**Salida (fracaso, estado ≠ 0):**
```python
{
    "estado": 1|2|3|4|-1,                     # int
    "mensaje": str,                           # descripción del error/estado
    "valor_z": None,
    "variables": None,
}
```

**Códigos de estado:**
- `0`: Optimización exitosa.
- `1`: Límite de iteraciones sin converger.
- `2`: Inviable (sin solución factible).
- `3`: No acotado.
- `4`: Problemas numéricos.
- `-1`: Error en datos de entrada o error interno.

---

## 4. Simplex Tabular (`src/models/simplex.py`)

### Clase: `SolucionadorSimplex`

#### Método: `resolver(datos_entrada: dict) -> dict`

**Propósito:** Resuelve problemas LP con restricciones **únicamente ≤** usando Simplex tabular.
Usa aritmética exacta con `fractions.Fraction`.

**Entrada:**
```python
{
    "tipo": "MAX" | "MIN",
    "objetivo": [c1, c2, ...],
    "restricciones": [
        {
            "coeficientes": [a1, a2, ...],
            "signo": "<=",                    # ⚠️ SÓLO ACEPTA "<="
            "rhs": valor
        },
        ...
    ]
}
```

**Salida (estado="optimo"):**
```python
{
    "estado": "optimo" | "no_acotado" | "requiere_otro_metodo" | "iviable",  # str
    "z_optimo": Fraction,                    # Fraction | None
    "variables_decision": [x1, x2, ...],     # list[Fraction] | None
    "encabezados": ["Base", "X1", "X2", "S1", "S2", "RHS"],  # list[str]
    "variables_base": ["S1", "S2"],          # list[str]: variable básica final de cada restricción
    "iteraciones": [
        {
            "tabla": np.ndarray (dtype=object),  # matriz numpy con Fraction
            "fila_pivote": int | None,
            "col_pivote": int | None,
            "mensaje": str
        },
        ...
    ]
}
```

**Salida (estado="requiere_otro_metodo"):**
```python
{
    "estado": "requiere_otro_metodo" | "iviable",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados": [],
    "variables_base": [],
    "iteraciones": []
}
```

---

## 5. Método de la M Grande (`src/models/m_grande.py`)

### Clase: `SolucionadorGranM`

#### Método: `resolver(datos_entrada: dict) -> dict`

**Propósito:** Resuelve problemas LP con restricciones **≤, ≥, ==** usando el método de la M Grande.
Aritmética exacta con `Fraction`. M = 10^9.

**Entrada:**
```python
{
    "tipo": "MAX" | "MIN",
    "objetivo": [c1, c2, ...],
    "restricciones": [
        {
            "coeficientes": [a1, a2, ...],
            "signo": "<=" | ">=" | "==",    # ✓ Acepta los 3 tipos
            "rhs": valor
        },
        ...
    ]
}
```

**Salida (estado="optimo"):**
```python
{
    "estado": "optimo" | "inviable" | "no_acotado",  # str
    "z_optimo": Fraction,                   # Fraction | None
    "variables_decision": [x1, x2, ...],    # list[Fraction] | None
    "encabezados": ["Base", "X1", "X2", "S1", "A1", "RHS"],  # list[str]
    "variables_base": ["A1", "X2"],         # list[str]
    "iteraciones": [
        {
            "tabla": np.ndarray (dtype=object),
            "fila_pivote": int | None,
            "col_pivote": int | None,
            "mensaje": str
        },
        ...
    ]
}
```

**Salida (estado="inviable" o "no_acotado"):**
```python
{
    "estado": "inviable" | "no_acotado",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados": [...],
    "variables_base": [...],
    "iteraciones": [...]
}
```

---

## 6. Método de Dos Fases (`src/models/dos_fases.py`)

### Clase: `SolucionadorDosFases`

#### Método: `resolver(datos_entrada: dict) -> dict`

**Propósito:** Resuelve problemas LP con restricciones **≤, ≥, ==** en dos fases.
Fase 1: minimiza W = ΣAi. Fase 2: optimiza Z original.
Usa `Fraction` para exactitud.

**Entrada:**
```python
{
    "tipo": "MAX" | "MIN",
    "objetivo": [c1, c2, ...],
    "restricciones": [
        {
            "coeficientes": [a1, a2, ...],
            "signo": "<=" | ">=" | "==",
            "rhs": valor
        },
        ...
    ]
}
```

**Salida (estado="optimo"):**
```python
{
    "estado": "optimo" | "inviable" | "no_acotado",  # str
    "z_optimo": Fraction,                   # Fraction | None
    "variables_decision": [x1, x2, ...],    # list[Fraction] | None
    "encabezados_f1": ["Base", "X1", "X2", "S1", "A1", "RHS"],  # Fase 1
    "encabezados_f2": ["Base", "X1", "X2", "S1", "RHS"],         # Fase 2
    "variables_base": [vars de la base final],
    "iteraciones": [
        {
            "fase": 1 | 2,                  # Identificador de fase
            "tabla": np.ndarray (dtype=object),
            "fila_pivote": int | None,
            "col_pivote": int | None,
            "mensaje": str
        },
        ...
    ]
}
```

**Salida (estado="inviable" o "no_acotado"):**
```python
{
    "estado": "inviable" | "no_acotado",
    "z_optimo": None,
    "variables_decision": None,
    "encabezados_f1": [...],
    "encabezados_f2": [...] o [],  # Fase 2 podría no existir si falló Fase 1
    "variables_base": [],
    "iteraciones": [...]  # Iteraciones de ambas fases
}
```

---

## 7. Utilidades: Graficador (`src/utils/graficador.py`)

### Función: `generar_grafico_cartesiano(problema: dict, resultado_resolucion: dict) -> str`

**Propósito:** Genera un gráfico cartesiano de la región factible en 2D (X1, X2).
Devuelve una cadena data-URI base64 para usarla en `ft.Image()`.

**Entrada:**
```python
problema = {
    "tipo": "MAX" | "MIN",
    "objetivo": [c1, c2],                   # Exactamente 2 coeficientes
    "restricciones": [
        {
            "coeficientes": [a1, a2],       # Exactamente 2 coeficientes cada una
            "signo": "<=" | ">=" | "==",
            "rhs": valor_numérico
        },
        ...
    ]
}

resultado_resolucion = {
    "estado": 0 o algún int,
    "variables": [x1, x2],                  # Debe haber exactamente 2
    "valor_z": float | None,
    ...
}
```

**Salida:**
```python
"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."  # str (data-URI) | None (en caso de error)
```

**Estructura interna del gráfico:**
- Ejes X1 (horizontal) e X2 (vertical).
- Líneas de restricciones dibujadas como líneas punteadas de distintos colores.
- Región factible rellena (si existe) en color morado (#4b2981) semitransparente.
- Vértices factibles como puntos.
- Punto óptimo marcado con círculo y anotación.
- Línea de isogonal (línea Z óptima) en color lima sólida.
- Leyenda en esquina superior derecha.

---

## Resumen de flujos de datos típicos

### Flujo 1: Guardar y resolver con método general
```
VistaIngreso._guardar_problema
  ↓
  arma datos_entrada {tipo, objetivo, restricciones}
  ↓
  Controlador.operar_problema(datos, 1)
  ↓
  HistorialDeProblemas.ingresar_problema(datos)
  ↓ devuelve datos
  ↓
  set_problema_activo(datos)
  
VistaGeneral.refresh()
  ↓
  Controlador.resolver_LP(problema, 1)
  ↓
  ResolutorGeneral.resolver(problema)
  ↓ devuelve {estado, valor_z, variables, mensaje}
  ↓
  Vista renderiza resultado
```

### Flujo 2: Consultar historial y resolver con Simplex
```
VistaHistorial.refresh()
  ↓
  Controlador.obtener_historial_de_problema()
  ↓
  HistorialDeProblemas.obtener_historial_de_problemas()
  ↓ devuelve list[dict]
  ↓
  Vista crea tarjetas

Usuario selecciona problema → _cargar_problema
  ↓
  set_problema_activo(problema) + Controlador.problema_activo = ...
  
VistaMatricial (opcion_resolucion=2).refresh()
  ↓
  Controlador.resolver_LP(problema, 2)
  ↓
  SolucionadorSimplex.resolver(problema)
  ↓ devuelve {estado, z_optimo, variables_decision, iteraciones, encabezados}
  ↓
  Vista renderiza tabla iterativa
```

### Flujo 3: Generar gráfico
```
VistaGrafica._generar_grafico(problema, resultado)
  ↓
  from src.utils.graficador import generar_grafico_cartesiano
  ↓
  generar_grafico_cartesiano(problema, resultado)
  ↓ devuelve data-URI base64
  ↓
  ft.Image(src=base64_uri)
```

---

## Notas técnicas importantes

1. **Aritmética exacta vs. flotante:**
   - `ResolutorGeneral` devuelve `float`.
   - `SolucionadorSimplex`, `SolucionadorGranM`, `SolucionadorDosFases` devuelven `Fraction`.
   - Cuando las vistas renderizan, convierten a string con `_formatear_valor()`.

2. **Restricciones de signos:**
   - `SolucionadorSimplex` **sólo** acepta `"<="`.
   - `SolucionadorGranM` y `SolucionadorDosFases` aceptan `"<="`, `">="`, `"=="`.
   - `ResolutorGeneral` (linprog) transforma `">=" → "<="` multiplicando por -1.

3. **Matrices en `iteraciones`:**
   - Numpy ndarray con dtype=object (para alojar Fraction).
   - Cada tabla incluye una columna "Base" al inicio.
   - Orden de columnas: `[Base | X1…Xn | S1…Sm | A1…Ap | RHS]`.
   - Fila 0 siempre es la función objetivo (Z o W en Dos Fases).

4. **Encabezados y nombres de variables:**
   - `"X1", "X2", ...` para variables de decisión.
   - `"S1", "S2", ...` para holguras y excesos.
   - `"A1", "A2", ...` para variables artificiales.
   - `"Base"` columna de etiquetas de variable básica.

5. **Gestión de problemas inviables:**
   - `ResolutorGeneral`: devuelve `estado=2`, `valor_z=None`, `variables=None`.
   - `SolucionadorGranM`: detecta artificiales en base con RHS > 0 → `estado="inviable"`.
   - `SolucionadorDosFases`: si Fase 1 devuelve W > 0 → declara `estado="inviable"`.

---

Fin del documento.

