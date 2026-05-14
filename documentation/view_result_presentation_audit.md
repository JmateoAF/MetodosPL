# Auditoria de presentacion de resultados en vistas

Fecha: 2026-05-14

## Objetivo
Verificar si las vistas que consumen resultados de los metodos de resolucion muestran correctamente todos los estados posibles.

Vistas auditadas:
- `ui/vista_general.py` (usa `Controlador.resolver_LP(..., 1)` -> `ResolutorGeneral`)
- `ui/vista_grafica.py` (usa `Controlador.resolver_LP(..., 1)` -> `ResolutorGeneral`)
- `ui/vista_matricial.py` (usa `Controlador.resolver_LP(..., 2|3|4)` -> `Simplex`, `GranM`, `DosFases`)

No aplica a esta auditoria:
- `ui/vista_ingreso.py`, `ui/vista_historial.py` (CRUD/estado, no presentan salidas de solvers directamente)

---

## 1) Estados esperados por metodo

### Metodo general (`ResolutorGeneral`, opcion 1)
Salida esperada:
- `estado = 0` (optimo)
- `estado = 1` (limite de iteraciones)
- `estado = 2` (inviable)
- `estado = 3` (no acotado)
- `estado = 4` (problema numerico)
- `estado = -1` (error de datos/interno)

### Simplex (`SolucionadorSimplex`, opcion 2)
Salida esperada:
- `estado = "optimo"`
- `estado = "no_acotado"`
- `estado = "inviable"` (parche reciente)
- `estado = "requiere_otro_metodo"`

### M Grande (`SolucionadorGranM`, opcion 3)
Salida esperada:
- `estado = "optimo"`
- `estado = "inviable"`
- `estado = "no_acotado"`

### Dos Fases (`SolucionadorDosFases`, opcion 4)
Salida esperada:
- `estado = "optimo"`
- `estado = "inviable"`
- `estado = "no_acotado"`

---

## 2) Resultado de la auditoria por vista

## Vista: `ui/vista_general.py`

### Cobertura
- `sin problema activo`: SI (mensaje warning)
- `resultado None`: SI (mensaje de error generico)
- `estado != 0`: SI (muestra error y mensaje backend)
- `estado == 0`: SI (muestra Z, variables y mensaje)

### Veredicto
- **CORRECTA para opcion 1**.
- Observacion UX: cuando hay error (`estado != 0`) deja `resultado_container` vacio; funcionalmente no rompe.

### Evidencia
- Logica principal: `ui/vista_general.py:95-101` y `ui/vista_general.py:103-130`.
- Prueba rapida ejecutada: devuelve `estado=3` y muestra estado en rojo con mensaje de backend.

---

## Vista: `ui/vista_grafica.py`

### Cobertura
- `sin problema activo`: SI
- `numero de variables != 2`: SI
- `resultado None`: SI
- `estado != 0`: **NO** (no hay rama de error por codigo de estado)
- `estado == 0`: SI

### Hallazgo
- **Falla funcional de presentacion**: para resultados no optimos (`estado=1,2,3,4,-1`) la vista marca exito:
  - `status_text = "Grafico generado correctamente."`
  - color verde
  - intenta renderizar grafico/resultados aunque no haya optimo real.

### Evidencia de codigo
- Falta validacion de `resultado.get("estado") == 0` en `ui/vista_grafica.py:128-143`.

### Evidencia de ejecucion
- Prueba con `estado=2` (inviable):
  - `status = "Grafico generado correctamente."`
  - color verde `#7ee081`

### Severidad
- **Alta** (mensaje de exito incorrecto para estado de fallo del solver).

---

## Vista: `ui/vista_matricial.py`

### Cobertura declarada
- `sin problema activo`: SI
- `resultado None`: SI
- `estado string de error/no optimo`: **PARCIAL/DEFECTUOSA**

### Hallazgo A (critico)
- **Crash** cuando `variables_decision` es `None`.
- En estados no optimos (`inviable`, `no_acotado`, `requiere_otro_metodo`) los modelos devuelven `variables_decision=None`.
- La vista hace `enumerate(resultado.get('variables_decision', []))` y al existir la clave con `None`, no usa `[]` -> produce `TypeError: 'NoneType' object is not iterable`.

#### Ubicacion
- `ui/vista_matricial.py:161-164`

#### Evidencia de ejecucion
- Instanciando `VistaMatricial` con resultado `estado='inviable'` + `variables_decision=None`:
  - error: `TypeError 'NoneType' object is not iterable`

### Hallazgo B (alta)
- **Estado visual superior incorrecto**: siempre marca exito verde cuando `resultado is not None`, sin distinguir `estado`.
- En `inviable`/`no_acotado`/`requiere_otro_metodo` deberia marcar warning/error.

#### Ubicacion
- `ui/vista_matricial.py:252-255`

### Hallazgo C (media)
- Para estados no optimos con `iteraciones=[]`, la tarjeta inicial se renderiza, pero el mensaje principal no es suficientemente semantico (depende del texto interno y no del estado global).

### Severidad
- **Critica** por crash en `variables_decision=None`.
- **Alta** por estado verde incorrecto en resultados no optimos.

---

## 3) Matriz de cumplimiento

| Vista | Metodo(s) | Estados cubiertos correctamente | Resultado |
|---|---|---|---|
| `vista_general` | opcion 1 | 0, 1, 2, 3, 4, -1 | OK |
| `vista_grafica` | opcion 1 | sin problema, vars!=2, None | PARCIAL (no diferencia `estado != 0`) |
| `vista_matricial` | opcion 2,3,4 | optimo parcial | NO OK (crash en no-optimos + estado visual incorrecto) |

---

## 4) Conclusiones

1. **No**, actualmente no todas las vistas presentan correctamente todos los posibles resultados.
2. `vista_general` esta bien para el metodo general.
3. `vista_grafica` muestra exito para estados no optimos (error de semantica UX).
4. `vista_matricial` tiene una regresion critica tras incluir `inviable` en Simplex:
   - no tolera `variables_decision=None`
   - puede romper la pantalla al recibir estados no optimos.

---

## 5) Recomendaciones concretas (sin aplicar cambios en esta auditoria)

1. En `vista_grafica.refresh()`, validar `resultado.get("estado") == 0` antes de marcar exito.
2. En `vista_matricial._renderizar_iteraciones()`, usar:
   - `variables = resultado.get("variables_decision") or []`
3. En `vista_matricial.refresh()`, colorear `status_text` segun `estado`:
   - verde solo para `optimo`
   - rojo/warning para `inviable`, `no_acotado`, `requiere_otro_metodo`
4. Mantener render de iteraciones cuando existan, incluso en no-optimos.

---

## 6) Comandos de verificacion usados

```powershell
python -u -c "import flet; print('flet_ok')"
```

```powershell
python -u -c "from ui.vista_grafica import VistaGrafica
class C:
    problema_activo={'tipo':'MAX','objetivo':[1,1],'restricciones':[{'coeficientes':[1,0],'signo':'<=','rhs':1},{'coeficientes':[0,1],'signo':'<=','rhs':1}]}
    def resolver_LP(self,p,o):
        return {'estado':2,'mensaje':'El problema es inviable (sin solucion factible).','valor_z':None,'variables':None}
v=VistaGrafica(C())
print('status=', v.status_text.value)
print('color=', v.status_text.color)"
```

```powershell
python -u -c "from ui.vista_matricial import VistaMatricial
class C:
    problema_activo={'tipo':'MAX','objetivo':[1],'restricciones':[{'coeficientes':[1],'signo':'<=','rhs':1}]}
    def resolver_LP(self,p,o):
        return {'estado':'inviable','z_optimo':None,'variables_decision':None,'encabezados':['Base','X1','RHS'],'variables_base':[],'iteraciones':[]}
v=VistaMatricial(C(),2,'Simplex','d')"
```

Resultado observado: `TypeError: 'NoneType' object is not iterable`.

---

Fin del reporte.

