# Informe: Comunicación entre archivos

Fecha: 2026-05-14

Resumen
-------
Este documento recoge el análisis estático del repositorio y describe cómo
se comunican los módulos/ficheros entre sí: dependencias (imports), flujo de
datos (qué estructuras se pasan), puntos de entrada y formatos de salida
esperados por cada capa (UI ⇄ Controlador ⇄ Models ⇄ Utils).

Estructura del proyecto (carpetas relevantes)
- `main.py` — punto de entrada (inicia Flet, crea `Controlador` y `NavigationApp`).
- `src/controller/controlador.py` — capa Controlador: orquesta llamadas a los solvers y al historial.
- `src/models/` — implementaciones de algoritmos:
  - `resolucion_rapida.py` (usa `scipy.optimize.linprog`)
  - `simplex.py` (Simplex tabular con Fraction)
  - `m_grande.py` (método de la M Grande)
  - `dos_fases.py` (Two-Phase Simplex)
  - `historial_de_problemas.py`
- `src/utils/graficador.py` — utilidades para generar gráficos (matplotlib → base64).
- `ui/` — vistas y navegación Flet: `navegacion.py`, `estado_ui.py`, `vista_*`.

Resumen de responsabilidades
- UI (carpeta `ui/`): crea widgets, construye diccionarios de entrada (`problema`) y
  muestra resultados. Usa `estado_ui` para compartir un `problema_activo` entre vistas
  y recibe una instancia del `Controlador` (pasada por `NavigationApp`).
- Controlador (`src/controller/controlador.py`): instancia los solvers y el historial,
  expone métodos: `resolver_LP(datos_entrada, opcion)` y `operar_problema(datos, opcion, indice)`
  y `obtener_historial_de_problema()` para la UI.
- Models (`src/models/`): implementan la lógica de resolución. Cada solver expone
  un método `resolver(datos_entrada)` que devuelve un diccionario con estructura
  dependiente del solver (ver más abajo).
- Utils: funciones auxiliares (gráficos) consumidas por la UI.

Import graph (nodos → importa → nodos)
- `main.py` → importa `src.controller.controlador.Controlador`, `ui.navegacion.NavigationApp`
- `src.controller.controlador` → importa:
  - `src.models.dos_fases.SolucionadorDosFases`
  - `src.models.historial_de_problemas.HistorialDeProblemas`
  - `src.models.m_grande.SolucionadorGranM`
  - `src.models.resolucion_rapida.ResolutorGeneral`
  - `src.models.simplex.SolucionadorSimplex`
- `ui/navegacion.py` → importa vistas desde `ui.*` y `ui.estado_ui`.
- Cada vista UI importa `ui.estado_ui` y recibe la instancia `controlador` desde `NavigationApp`.
- `ui/vista_grafica.py` → además importa `src.utils.graficador.generar_grafico_cartesiano` en tiempo de ejecución
  dentro de `_generar_grafico`.

Comunicación y flujo de datos (pormenorizado)
-------------------------------------------
1) Creación y paso del controlador
   - `main.py` crea `controlador = Controlador()` y luego `NavigationApp(page, controlador)`.
   - `NavigationApp` guarda `self.controlador` y se la pasa (por constructor) a las vistas
     (`VistaIngreso`, `VistaHistorial`, `VistaGeneral`, `VistaGrafica`, `VistaMatricial`).

2) Estado compartido del problema activo
   - `ui/estado_ui.py` define `problema_activo` (variable global) y funciones:
     `set_problema_activo(datos)` y `get_problema_activo()`.
   - Muchas vistas usan `get_problema_activo()` como respaldo; algunas vistas además
     actualizan `self.controlador.problema_activo` mediante `setattr(...)` y llaman
     `set_problema_activo(...)`. Por tanto hay dos vías de estado:
       a) Atributo dinámico `problema_activo` en la instancia `controlador` (no está
          formalizado en la clase Controlador, pero se usa por convención).
       b) Variable global en `ui.estado_ui` usada por las vistas para compartir estado
          sin tocar la capa `src/`.

3) Guardado y recuperación de problemas (Historial)
   - `VistaIngreso._guardar_problema` crea el diccionario de entrada con la forma:
       {
         "tipo": "MAX"|"MIN",
         "objetivo": [coef1, coef2, ...],
         "restricciones": [ {"coeficientes": [...], "signo": "<=|>=|==", "rhs": valor}, ... ]
       }
   - Llama `self.controlador.operar_problema(datos_entrada, 1)` para guardar.
   - `Controlador.operar_problema` (opción 1) delega a `HistorialDeProblemas.ingresar_problema`.
   - `VistaHistorial` invoca `controlador.obtener_historial_de_problema()` y `operar_problema(...,3,indice)`
     para eliminar.

4) Resolución de problemas
   - UI (vistas) llaman `controlador.resolver_LP(problema, opcion)` con `opcion`:
       1 → método general (resolucion_rapida.ResolutorGeneral)
       2 → Simplex (src.models.simplex.SolucionadorSimplex)
       3 → M Grande (src.models.m_grande.SolucionadorGranM)
       4 → Dos Fases (src.models.dos_fases.SolucionadorDosFases)
   - `Controlador.resolver_LP` simplemente invoca el solver correspondiente y devuelve
     su diccionario de resultado a la vista.

5) Renderizado y formatos esperados
   - `resolucion_rapida.ResolutorGeneral.resolver` devuelve dict con claves:
       - `estado` (int): códigos similares a scipy (0=óptimo)
       - `mensaje` (str)
       - `valor_z` (float|None)
       - `variables` (list|None) — [x1,x2,...]
     Vistas que usan este formato: `vista_general.py`, `vista_grafica.py`.

   - `simplex.SolucionadorSimplex`, `m_grande.SolucionadorGranM`, `dos_fases.SolucionadorDosFases`
     devuelven un diccionario orientado a mostrar iteraciones, por ejemplo contienen:
       - `estado` (str) — p.ej. "optimo", "no_acotado", "inviable", etc.
       - `z_optimo` (Fraction|None)
       - `variables_decision` (list[Fraction]|None)
       - `encabezados` o `encabezados_f1`/`encabezados_f2` (listas de nombres de columnas)
       - `iteraciones` (list[dict]) — cada entrada contiene `tabla` (numpy ndarray dtype object)
     Vistas que consumen estas salidas: `vista_matricial.py` (espera `iteraciones`, `encabezados`),
     `vista_grafica.py` y `vista_general.py` pueden consumir la forma simplificada devuelta por
     `resolucion_rapida`.

6) Uso de utilidades
   - `vista_grafica._generar_grafico` importa y usa `src.utils.graficador.generar_grafico_cartesiano(problema, resultado)`
     y espera una cadena data-URI base64 para `ft.Image(src=...)`.

Notas importantes y observaciones
---------------------------------
- Controlador crea instancias de los solvers y del historial a nivel de clase (atributos
  estáticos de clase). Esto hace que haya una sola instancia compartida por todas las instancias
  de `Controlador` (aunque en práctica sólo se crea una en `main.py`). Es intencional pero
  conviene documentarlo. Si se quisiera aislamiento por instancia, mover esos objetos al `__init__`.

- El intercambio de estado `problema_activo` se hace por dos vías (atributo dinámico del controlador
  y variable global en `ui.estado_ui`). Esto funciona pero puede confundir (duplicación de fuente de verdad).
  Recomendación: elegir una única fuente de verdad (preferible: el `Controlador`) y usar métodos formales
  para set/get; o bien mantener `estado_ui` y eliminar el uso de `controlador.problema_activo`.

- Formatos devueltos por los modelos no están normalizados entre el "resolver rápido" (linprog)
  y los solvers tabulares. Las vistas ya manejan esto (cada vista usa el formato que necesita), pero
  documentarlo (como aquí) ayuda a mantener compatibilidad.

- `vista_grafica` importa `src.utils.graficador` dentro del método `_generar_grafico` (import bajo demanda)
  lo cual evita importar matplotlib en tiempo de carga de la UI (buena práctica para reducir tiempo de inicio
  y problemas en entornos sin GUI). `graficador` usa `matplotlib.use('agg')` y devuelve data-URI base64 —
  diseño apropiado para Flet.

Mapa conciso de llamadas (ejemplo de flujo típico)
------------------------------------------------
1) Usuario abre app → `main.py` → `Controlador()` → `NavigationApp` → muestra `VistaIngreso`.
2) Usuario rellena formulario y pulsa "Guardar" → `VistaIngreso._guardar_problema`:
   - arma `datos_entrada` (dict) → `controlador.operar_problema(datos, 1)` → `HistorialDeProblemas.ingresar_problema`
   - llama `set_problema_activo(datos)` y `setattr(controlador, 'problema_activo', datos)`.
3) Usuario va a "Solución Rápida" → `VistaGeneral.refresh`:
   - obtiene `problema` desde `controlador.problema_activo` o `get_problema_activo()`;
   - llama `controlador.resolver_LP(problema, 1)` → `ResolutorGeneral.resolver` (linprog) → devuelve dict con `valor_z`, `variables`.
   - `VistaGeneral` muestra los resultados.
4) Usuario va a "Simplex" → `NavigationApp` crea `VistaMatricial(..., opcion_resolucion=2)` →
   - `VistaMatricial.refresh` llama `controlador.resolver_LP(problema, 2)` → `SolucionadorSimplex.resolver`
   - devuelve `iteraciones` y `encabezados` que la vista renderiza en tablas.

Archivos analizados (paths)
- \Software_IO_PL\main.py
- \Software_IO_PL\src\controller\controlador.py
- \Software_IO_PL\src\models\historial_de_problemas.py
- \Software_IO_PL\src\models\resolucion_rapida.py
- \Software_IO_PL\src\models\simplex.py
- \Software_IO_PL\src\models\m_grande.py
- \Software_IO_PL\src\models\dos_fases.py
- \Software_IO_PL\src\utils\graficador.py
- \Software_IO_PL\ui\navegacion.py
- \Software_IO_PL\ui\estado_ui.py
- \Software_IO_PL\ui\vista_general.py
- \Software_IO_PL\ui\vista_grafica.py
- \Software_IO_PL\ui\vista_historial.py
- \Software_IO_PL\ui\vista_ingreso.py
- \Software_IO_PL\ui\vista_matricial.py

Conclusión y siguientes pasos sugeridos
--------------------------------------
- El diseño general sigue una arquitectura MVC clara: UI (Flet) ↔ Controlador ↔ Models.
- Recomendaciones sencillas:
  1. Normalizar la fuente de verdad para `problema_activo` (preferir el `Controlador`).
  2. Documentar en `Controlador` que las instancias de solver son singletons a nivel de clase.
  3. Añadir docstrings/tipos explícitos en `Controlador` para `problema_activo` si se va a usar.

El informe ha sido guardado en este fichero. Si quieres, puedo:
- generar automáticamente un diagrama DOT / imagen del grafo de importaciones, o
- producir un JSON machine-readable con el grafo y los formatos de mensajes, o
- normalizar el acceso a `problema_activo` y aplicar un cambio mínimo en el código.

