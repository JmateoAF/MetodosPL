# Plan de Expansión Detallado: Software de Investigación de Operaciones (MVP v1.0)

Este documento detalla la hoja de ruta estratégica para la evolución del software de optimización lineal desarrollado en Flet (v0.85). El objetivo es transformar el Producto Mínimo Viable (MVP) actual en una plataforma robusta, profesional y con capacidades analíticas avanzadas.

---

## 1. Fase de Estabilidad y Pulido Visual (Inmediata)

### 1.1. Resaltado de Pivotes en Vistas Matriciales
* **Objetivo:** Mejorar la capacidad pedagógica de las vistas de Simplex, M-Grande y Dos Fases.
* **Detalle:** Implementar lógica en el renderizado de `ft.DataTable` para resaltar dinámicamente la **columna pivote**, la **fila pivote** y el **elemento pivote** utilizando el color de acento del sistema (`#4b2981`).
* **Implementación:** El backend ya entrega los índices de pivote; la UI debe aplicar estilos condicionales en las celdas correspondientes.

### 1.2. Optimización de Tablas y Visualización
* **Scroll Bidireccional:** Asegurar que todas las tablas matriciales cuenten con `ft.ScrollMode.AUTO` tanto horizontal como verticalmente para manejar problemas de gran escala sin romper el layout.
* **Comparativa de Iteraciones:** Organizar las tablas de entrada y salida de variables en una disposición que facilite el seguimiento del algoritmo (antes y después de la iteración).

---

## 2. Fase de Flexibilidad en el Ingreso de Problemas

### 2.1. Motor de Parsing de Texto (src/utils/parser.py)
Se desarrollará un módulo independiente basado en Expresiones Regulares (Regex) para interpretar dos nuevos formatos:

* **Formato Natural (Algebraico):**
    * Interpretación de cadenas como: `Max Z = 3x1 + 5x2 - 2x3`, `x1 + x3 <= 10`.
    * Detección inteligente de coeficientes implícitos (ej. `x1` -> `1`, `-x2` -> `-1`).
    * Tolerancia a espacios y orden de variables.
* **Formato por Coeficientes (CSV):**
    * Entrada rápida mediante comas: `Max, 3, 5, -2`.
    * Estructura simplificada para restricciones: `1, 0, 2, <=, 10`.

### 2.2. Validación de Sintaxis en Tiempo Real
* Implementar un validador en las nuevas vistas de ingreso que alerte al usuario sobre errores de escritura (ej. signos duplicados, falta de variables) antes de intentar procesar el problema.

---

## 3. Fase de Gestión de Archivos e Interoperabilidad (I/O)

### 3.1. Barra de Herramientas Superior (AppBar / MenuBar)
* **Menú Archivo:** Opciones de "Importar", "Exportar", "Guardar Historial" y "Cargar Historial".
* **Menú Ver:** Cambiar entre los modos de ingreso (Matricial, Natural, Coeficientes).
* **Menú Editar:** Cambiar entre las ventanas de para operar con los problemas (Ingreso, Historial de problemas).
* **Menú Resolver:** Cambiar entre las ventanas de los 5 tipos de resolución (Resolución rápida, Método gráfico, Simplex, M grande, Dos fases.).
* **Menú Ayuda:** Acceso a la sección "Sobre Nosotros" y créditos.

### 3.2. Persistencia y Exportación
* **Exportación de Resultados:** Capacidad de exportar el informe final de resolución (Z óptimo, variables, mensajes) a formatos `.txt` o `.csv`.
* **Gestión del Historial:**
    * **Guardar:** Serializar el historial completo de problemas en un archivo `.json` o `.txt` estructurado.
    * **Cargar:** Restaurar una sesión previa importando el archivo de historial guardado.
* **Integración FilePicker:** Uso de `ft.FilePicker` para interactuar con el sistema de archivos del SO de forma segura.

### 3.3. Sección "Sobre Nosotros" y Créditos
* Incluir una sección informativa accesible desde el menú "Ayuda" que detalle el propósito del software, los autores y las fuentes de inspiración (ej. libros de texto, cursos).

---

## 4. Fase de Analítica Avanzada y Rigor Matemático

### 4.1. Análisis de Sensibilidad (Post-Optimalidad)
Aprovechar las capacidades de `scipy.optimize.linprog` y los solvers tabulares para mostrar:
* **Precios Sombra (Shadow Prices):** Valor marginal de los recursos.
* **Variables de Holgura y Exceso (Slack/Surplus):** Identificación de recursos sobrantes.
* **Rangos de Coeficientes y RHS:** Límites en los que la base actual se mantiene óptima.

### 4.2. Programación Entera Lineal (ILP)
* Integración de algoritmos especializados como **Branch and Bound** (Ramificación y Acotamiento) o **Planos de Corte** para problemas donde las variables deben ser estrictamente enteras.

---

## 5. Fase de Refactorización Arquitectónica

### 5.1. Transición a Programación Orientada a Objetos (Backend)
* Migrar el almacenamiento de problemas de diccionarios planos a **Clases de Python**.
* Beneficio: Facilitará la implementación de métodos complejos de sensibilidad y permitirá una validación de datos más estricta desde la creación del objeto.

### 5.2. Robustez ante Casos Especiales
* Mejorar la detección y comunicación visual de estados como **Infactibilidad**, **No Acotamiento** y **Degeneración** en todas las vistas de resolución.

---

**Nota:** El desarrollo seguirá un enfoque incremental, priorizando la estabilidad del núcleo matemático y la consistencia visual antes de añadir nuevas lógicas de optimización avanzada.
