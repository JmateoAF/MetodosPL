# Optimizador Lineal - Investigación de Operaciones

Software interactivo desarrollado en Python para la resolución y análisis de problemas de Programación Lineal. El proyecto está enfocado en proporcionar tanto la solución matemática óptima como el desglose procedimental de los algoritmos clásicos de optimización, diseñado específicamente como herramienta de apoyo para el estudio de Investigación de Operaciones.

## Características Principales

La aplicación cuenta con una interfaz gráfica (GUI) intuitiva que ofrece 5 módulos principales:

1. **Solución Directa (Solver General):** Un módulo de resolución rápida que omite el paso a paso matricial y entrega el resultado final instantáneamente.
2. **Método Gráfico Interactivo:** Permite resolver problemas de 2 variables. Incluye un plano cartesiano donde la función objetivo y las restricciones son visibles.
3. **Método Simplex (Paso a Paso):** Resolución tabular que muestra cada iteración (tableau) hasta alcanzar la solución óptima, ideal para el seguimiento académico del algoritmo.
4. **Método de la M Grande:** Extensión del método tabular para problemas que requieren variables artificiales, mostrando el impacto de la penalización $M$ en cada matriz.
5. **Método de las Dos Fases:** Desglose del problema en la Fase I (minimización de variables artificiales) y Fase II (optimización de la función objetivo original), con sus respectivas tablas.

## Arquitectura del Software

El proyecto está estructurado bajo el patrón de diseño **Modelo-Vista-Controlador (MVC)** para separar estrictamente la lógica matemática de la interfaz de usuario:

* **Modelos (`src/modelos/`):** Contiene la lógica pura de Python. Aquí se ejecutan los cálculos, pivoteos de matrices y algoritmos (sin dependencias de interfaz gráfica).
* **Vistas (`ui/`):** Desarrolladas íntegramente con Flet para garantizar facilidad de uso y resultados visuales modernos. Por a su naturaleza multiplataforma, el mismo código permite ejecutar la aplicación de forma nativa en escritorio, navegadores web o dispositivos móviles.
* **Controladores (`src/controladores/`):** Actúan como puente. Capturan los datos ingresados por el usuario, los envían a los modelos matemáticos, y posteriormente inyectan los resultados numéricos y las gráficas en las vistas.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.x 
* **Interfaz Gráfica:** Flet 0.85.0 
* **Gráficos:** Matplotlib
* **Cálculo Numérico y Solución Directa:** NumPy, SciPy / PuLP

## Instalación y Ejecución

1. Clonar el repositorio.
```bash
   git clone https://github.com/LeonardoByte/Software_IO_PL
   cd Software_IO_PL
```

2. Se recomienda crear y activar un entorno virtual (`.venv`):
```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/macOS:
   source .venv/bin/activate
   ```

3. Instalar dependencias: Con el entorno virtual activado, instale todos los paquetes necesarios definidos en el archivo requirements.txt:
```bash
   pip install -r requirements.txt
```
4. Ejecutar la aplicación: Inicie el programa ejecutando el archivo principal (asegúrese de estar en la raíz del proyecto):
```bash
   python main.py
```