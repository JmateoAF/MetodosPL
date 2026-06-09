# src.utils/graficador.py
"""
graficador.py
=============
Módulo de utilidades para generar representaciones gráficas bidimensionales (2D).
Diseño Thread-safe mediante el uso explícito del backend 'agg' de Matplotlib 
para garantizar una ejecución asíncrona libre de bloqueos en la interfaz de Flet.

Responsabilidades:
    - Interpretar las entidades de dominio inmutables ProblemaPL y RespuestaSciPyPL.
    - Calcular geométricamente las restricciones, vértices y polígonos de la región factible.
    - Retornar el lienzo renderizado como una cadena en formato data-URI base64.

Autor: Utilities Graphics Module — MVC Linear Optimizer
"""

import base64
from io import BytesIO
from typing import List, Tuple, Optional
import numpy as np

import matplotlib
matplotlib.use('agg')  # Forzar backend no interactivo para evitar fallos de renderizado
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

# Importaciones estrictas de las entidades orientadas a objetos del dominio
from src.models.entity.enums import EstadoProblema, SignoRestriccion
from src.models.entity.problema import ProblemaPL, Restriccion
from src.models.entity.respuesta import RespuestaSciPyPL


def _fig_to_base64(fig: Figure) -> str:
    """Convierte la figura de Matplotlib en una cadena data-URI codificada en Base64."""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', transparent=True, dpi=100)
    plt.close(fig)
    base64_codificado = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{base64_codificado}"


def _recta_en_canvas(a: float, b: float, c: float, x_max: float, y_max: float) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Calcula los puntos de intersección exactos de una línea recta canónica 
    (a*x1 + b*x2 = c) con los límites del canvas rectangular definido en el plano.
    
    Retorna
    -------
    Optional[Tuple[np.ndarray, np.ndarray]]
        Tupla con las coordenadas (xs, ys) de los extremos visibles, o None si no intersecta.
    """
    EPSILON = 1e-9
    candidatos: List[Tuple[float, float]] = []

    # Borde inferior (x2 = 0) -> a * x1 = c
    if abs(a) > EPSILON:
        x1 = c / a
        if -EPSILON <= x1 <= x_max + EPSILON:
            candidatos.append((float(np.clip(x1, 0, x_max)), 0.0))

    # Borde superior (x2 = y_max) -> a * x1 = c - b * y_max
    if abs(a) > EPSILON:
        x1 = (c - b * y_max) / a
        if -EPSILON <= x1 <= x_max + EPSILON:
            candidatos.append((float(np.clip(x1, 0, x_max)), float(y_max)))

    # Borde izquierdo (x1 = 0) -> b * x2 = c
    if abs(b) > EPSILON:
        x2 = c / b
        if -EPSILON <= x2 <= y_max + EPSILON:
            candidatos.append((0.0, float(np.clip(x2, 0, y_max))))

    # Borde derecho (x1 = x_max) -> b * x2 = c - a * x_max
    if abs(b) > EPSILON:
        x2 = (c - a * x_max) / b
        if -EPSILON <= x2 <= y_max + EPSILON:
            candidatos.append((float(x_max), float(np.clip(x2, 0, y_max))))

    # Remover duplicados originados en los vértices del canvas
    puntos_unicos: List[Tuple[float, float]] = []
    for punto in candidatos:
        if not any(abs(punto[0] - u[0]) < EPSILON and abs(punto[1] - u[1]) < EPSILON for u in puntos_unicos):
            puntos_unicos.append(punto)

    if len(puntos_unicos) < 2:
        return None

    if len(puntos_unicos) > 2:
        mejor_par = max(
            ((i, j) for i in range(len(puntos_unicos)) for j in range(i + 1, len(puntos_unicos))),
            key=lambda ij: (puntos_unicos[ij[0]][0] - puntos_unicos[ij[1]][0]) ** 2
                           + (puntos_unicos[ij[0]][1] - puntos_unicos[ij[1]][1]) ** 2,
        )
        puntos_unicos = [puntos_unicos[mejor_par[0]], puntos_unicos[mejor_par[1]]]

    xs = np.array([puntos_unicos[0][0], puntos_unicos[1][0]])
    ys = np.array([puntos_unicos[0][1], puntos_unicos[1][1]])
    return xs, ys


def generar_grafico_cartesiano(problema: ProblemaPL, resultado_resolucion: RespuestaSciPyPL) -> Optional[str]:
    """
    Genera un gráfico 2D de la región factible y la función objetivo del modelo de PL.

    Parámetros
    ----------
    problema : ProblemaPL
        Entidad inmutable que encapsula las variables y restricciones del modelo matemático.
    resultado_resolucion : RespuestaSciPyPL
        Entidad inmutable con los resultados de optimización devueltos por SciPy.

    Retorna
    -------
    Optional[str]
        Cadena de caracteres que contiene la imagen PNG codificada en un URI de Base64, 
        o None si se produce una excepción interna catastrófica.
    """
    try:
        # Inicializar el lienzo con estética oscura adaptada a la interfaz del sistema
        fig, ax = plt.subplots(figsize=(9, 9), facecolor='#1e1e1e')
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')

        ax.set_xlabel("X1", color='white', fontsize=12)
        ax.set_ylabel("X2", color='white', fontsize=12)
        ax.set_title("Método Gráfico - Región Factible", color='white', fontsize=14, fontweight='bold')
        ax.grid(True, linestyle="--", alpha=0.3, color='gray')

        # --- 1. Extracción e inicialización segura de los puntos óptimos ---
        x_opt: float = 0.0
        y_opt: float = 0.0
        z_opt: Optional[float] = None

        if resultado_resolucion.estado == EstadoProblema.OPTIMO:
            # Uso seguro de las propiedades inmutables de la respuesta analítica
            vector_x = resultado_resolucion.x
            if vector_x is not None and len(vector_x) >= 2:
                x_opt = float(vector_x[0])
                y_opt = float(vector_x[1])
            
            if resultado_resolucion.fun is not None:
                z_opt = float(resultado_resolucion.fun)

        # --- 2. Construcción matemática del sistema de ecuaciones (Ejes cartesianos como cotas) ---
        ecuaciones: List[Tuple[float, float, float]] = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        
        for restriccion in problema.restricciones:
            if len(restriccion.coeficientes) >= 2:
                # Acceso directo OO a la lista tipada de coeficientes algebraicos
                ecuaciones.append((
                    float(restriccion.coeficientes[0]), 
                    float(restriccion.coeficientes[1]), 
                    float(restriccion.rhs)
                ))

        # --- 3. Cálculo de intersecciones teóricas en el plano euclidiano ---
        puntos_interseccion: List[Tuple[float, float]] = []
        for i in range(len(ecuaciones)):
            for j in range(i + 1, len(ecuaciones)):
                a1, b1, c1 = ecuaciones[i]
                a2, b2, c2 = ecuaciones[j]
                determinante = a1 * b2 - a2 * b1
                
                if abs(determinante) > 1e-9:
                    x = (c1 * b2 - c2 * b1) / determinante
                    y = (a1 * c2 - a2 * c1) / determinante
                    if x >= -1e-6 and y >= -1e-6:
                        puntos_interseccion.append((x, y))

        # --- 4. Filtrado funcional de vértices factibles ---
        vertices_factibles: List[Tuple[float, float]] = []
        for x, y in puntos_interseccion:
            es_factible = True
            
            for restriccion in problema.restricciones:
                if len(restriccion.coeficientes) < 2:
                    continue
                
                c1 = float(restriccion.coeficientes[0])
                c2 = float(restriccion.coeficientes[1])
                limite_rhs = float(restriccion.rhs)
                evaluacion = c1 * x + c2 * y

                if restriccion.signo == SignoRestriccion.MENOR_IGUAL and evaluacion > limite_rhs + 1e-6:
                    es_factible = False
                    break
                elif restriccion.signo == SignoRestriccion.MAYOR_IGUAL and evaluacion < limite_rhs - 1e-6:
                    es_factible = False
                    break
                elif restriccion.signo == SignoRestriccion.IGUAL and abs(evaluacion - limite_rhs) > 1e-6:
                    es_factible = False
                    break

            if es_factible and not any(abs(v[0] - x) < 1e-5 and abs(v[1] - y) < 1e-5 for v in vertices_factibles):
                vertices_factibles.append((x, y))

        # --- 5. Determinación de límites dinámicos para el encuadre ---
        max_x = max([p[0] for p in puntos_interseccion] + [x_opt, 10.0]) if puntos_interseccion else 10.0
        max_y = max([p[1] for p in puntos_interseccion] + [y_opt, 10.0]) if puntos_interseccion else 10.0

        max_x_grafico = float(max_x) * 1.15 if max_x > 0 else 10.0
        max_y_grafico = float(max_y) * 1.15 if max_y > 0 else 10.0

        # --- 6. Dibujar área geométrica relleno de la Región Factible ---
        if len(vertices_factibles) >= 3:
            cx = sum(v[0] for v in vertices_factibles) / len(vertices_factibles)
            cy = sum(v[1] for v in vertices_factibles) / len(vertices_factibles)
            vertices_ordenados = sorted(vertices_factibles, key=lambda v: np.arctan2(v[1] - cy, v[0] - cx))
            
            poligono = Polygon(vertices_ordenados, facecolor='#4b2981', alpha=0.4, edgecolor='none')
            ax.add_patch(poligono)
        elif len(vertices_factibles) == 1:
            ax.plot(vertices_factibles[0][0], vertices_factibles[0][1], 'ro', markersize=8)
        elif len(vertices_factibles) == 2:
            ax.plot([vertices_factibles[0][0], vertices_factibles[1][0]], [vertices_factibles[0][1], vertices_factibles[1][1]],
                    color='#4b2981', linewidth=3, alpha=0.5)

        # --- 7. Trazado de las rectas correspondientes a cada restricción ---
        colores_restricciones: List[str] = ['#e6194b', '#1e88e5', '#3cb44b', '#f58231', '#911eb4', '#46f0f0', '#f032e6']
        for idx, restriccion in enumerate(problema.restricciones):
            if len(restriccion.coeficientes) < 2:
                continue

            c1 = float(restriccion.coeficientes[0])
            c2 = float(restriccion.coeficientes[1])
            limite_rhs = float(restriccion.rhs)
            color_asignado = colores_restricciones[idx % len(colores_restricciones)]

            if abs(c1) < 1e-9 and abs(c2) < 1e-9:
                continue

            interseccion_canvas = _recta_en_canvas(c1, c2, limite_rhs, max_x_grafico, max_y_grafico)
            if interseccion_canvas is not None:
                xs, ys = interseccion_canvas
                ax.plot(xs, ys, color=color_asignado, linestyle='--', label=f"R{idx+1}", alpha=0.8, linewidth=1.6)

        # --- 8. Trazado de la Isocuanta Óptima (Línea de nivel de la función objetivo) ---
        if len(problema.objetivo) >= 2 and z_opt is not None:
            c1_obj = float(problema.objetivo[0])
            c2_obj = float(problema.objetivo[1])

            if abs(c1_obj) > 1e-9 or abs(c2_obj) > 1e-9:
                try:
                    interseccion_objetivo = _recta_en_canvas(c1_obj, c2_obj, z_opt, max_x_grafico, max_y_grafico)
                    if interseccion_objetivo is not None:
                        xs_obj, ys_obj = interseccion_objetivo
                        ax.plot(xs_obj, ys_obj, color='lime', linewidth=2.5, linestyle='-',
                                label=f'Z óptima = {z_opt:.2f}', alpha=0.9, zorder=5)
                except Exception:
                    pass

        # --- 9. Ubicación formal del marcador geométrico del vértice óptimo ---
        if resultado_resolucion.estado == EstadoProblema.OPTIMO:
            ax.plot(x_opt, y_opt, marker='o', color='gold', markersize=14,
                    markeredgecolor='white', markeredgewidth=2.5, label=f'Óptimo: Z={z_opt:.2f}',
                    linestyle='none', zorder=10)
            ax.annotate(f'({x_opt:.2f}, {y_opt:.2f})', xy=(x_opt, y_opt),
                        xytext=(x_opt + max_x_grafico * 0.03, y_opt + max_y_grafico * 0.03),
                        color='gold', fontsize=10, fontweight='bold', zorder=11)

        ax.set_xlim(0, max_x_grafico)
        ax.set_ylim(0, max_y_grafico)
        ax.legend(loc="upper right", facecolor='#1e1e1e', labelcolor='white', fontsize=9)

        plt.tight_layout()
        return _fig_to_base64(fig)
        
    except Exception as error_grafico:
        print(f"Error crítico detectado en generar_grafico_cartesiano: {error_grafico}")
        return None
    