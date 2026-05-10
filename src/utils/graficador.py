"""
graficador.py
=============
Módulo de utilidades para generar gráficos con Matplotlib.
Thread-safe con matplotlib.use('agg') para evitar bloqueos en Flet.
Retorna imágenes codificadas en base64 para compatibilidad con ft.Image.
"""

import base64
from io import BytesIO

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np


def _safe_float(valor, default=0.0):
    """Convierte cualquier valor a float de forma segura, incluye Fraction, np.float64, etc."""
    try:
        if hasattr(valor, "item"):
            valor = valor.item()
        return float(valor)
    except Exception:
        return default


def _fig_to_base64(fig) -> str:
    """Convierte figura de Matplotlib a data URI base64 para Flet."""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=100)
    plt.close(fig)
    b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"


def generar_grafico_cartesiano(problema: dict, resultado_resolucion: dict) -> str:
    """Genera gráfico cartesiano con restricciones y región factible."""
    try:
        fig, ax = plt.subplots(figsize=(9, 9), facecolor='#1e1e1e')
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')

        ax.set_xlabel("X1", color='white', fontsize=12)
        ax.set_ylabel("X2", color='white', fontsize=12)
        ax.set_title("Método Gráfico - Región Factible", color='white', fontsize=14, fontweight='bold')
        ax.grid(True, linestyle="--", alpha=0.3, color='gray')

        restricciones = problema.get("restricciones", []) or []

        # Extraer óptimo del resultado
        x_opt, y_opt, z_opt = 0.0, 0.0, None
        if resultado_resolucion and resultado_resolucion.get("estado") == 0:
            variables = resultado_resolucion.get("variables") or []
            if len(variables) >= 2:
                x_opt = _safe_float(variables[0], 0.0)
                y_opt = _safe_float(variables[1], 0.0)
            z_opt = _safe_float(resultado_resolucion.get("valor_z"), None)

        # Construir ecuaciones de restricciones
        ecuaciones = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        for r in restricciones:
            coefs = r.get("coeficientes", [])
            if len(coefs) >= 2:
                ecuaciones.append((_safe_float(coefs[0]), _safe_float(coefs[1]), _safe_float(r.get("rhs", 0.0))))

        # Calcular intersecciones
        puntos = []
        for i in range(len(ecuaciones)):
            for j in range(i + 1, len(ecuaciones)):
                a1, b1, c1 = ecuaciones[i]
                a2, b2, c2 = ecuaciones[j]
                det = a1 * b2 - a2 * b1
                if abs(det) > 1e-9:
                    x = (c1 * b2 - c2 * b1) / det
                    y = (a1 * c2 - a2 * c1) / det
                    if x >= -1e-6 and y >= -1e-6:
                        puntos.append((x, y))

        # Filtrar vértices factibles
        vertices = []
        for x, y in puntos:
            es_factible = True
            for r in restricciones:
                coefs = r.get("coeficientes", [])
                if len(coefs) < 2:
                    continue
                c1 = _safe_float(coefs[0])
                c2 = _safe_float(coefs[1])
                rhs = _safe_float(r.get("rhs", 0.0))
                signo = r.get("signo", "<=")
                val = c1 * x + c2 * y

                if signo == "<=" and val > rhs + 1e-6:
                    es_factible = False
                    break
                elif signo == ">=" and val < rhs - 1e-6:
                    es_factible = False
                    break
                elif signo == "==" and abs(val - rhs) > 1e-6:
                    es_factible = False
                    break

            if es_factible and not any(abs(v[0] - x) < 1e-5 and abs(v[1] - y) < 1e-5 for v in vertices):
                vertices.append((x, y))

        # Calcular límites dinámicos
        max_x = max([p[0] for p in puntos] + [x_opt, 10.0]) if puntos else 10.0
        max_y = max([p[1] for p in puntos] + [y_opt, 10.0]) if puntos else 10.0

        max_x_grafico = float(max_x) * 1.15 if max_x > 0 else 10.0
        max_y_grafico = float(max_y) * 1.15 if max_y > 0 else 10.0

        # Dibujar región factible
        if len(vertices) >= 3:
            cx = sum(v[0] for v in vertices) / len(vertices)
            cy = sum(v[1] for v in vertices) / len(vertices)
            vertices_ord = sorted(vertices, key=lambda v: np.arctan2(v[1] - cy, v[0] - cx))
            poly = plt.Polygon(vertices_ord, facecolor='#4b2981', alpha=0.4, edgecolor='none')
            ax.add_patch(poly)
        elif len(vertices) == 1:
            ax.plot(vertices[0][0], vertices[0][1], 'ro', markersize=8)
        elif len(vertices) == 2:
            ax.plot([vertices[0][0], vertices[1][0]], [vertices[0][1], vertices[1][1]],
                    color='#4b2981', linewidth=3, alpha=0.5)

        # -----------------------------------------------------------------------
        # Función auxiliar: intersección de la recta  a·x + b·y = c
        # con el rectángulo del canvas [0, x_max] × [0, y_max].
        #
        # Estrategia: candidateamos los 4 bordes del canvas como segmentos
        # paramétricos y retenemos solo los puntos que caen dentro del canvas.
        # Esto funciona para cualquier combinación de signos de a y b,
        # incluyendo rectas con pendiente negativa, rectas que entran/salen
        # por los bordes superior/derecho y casos puramente verticales u
        # horizontales. Devuelve exactamente 2 puntos o None si la recta
        # no cruza el área visible.
        # -----------------------------------------------------------------------
        def _recta_en_canvas(a, b, c, x_max, y_max):
            """
            Calcula los dos puntos de intersección de a·x + b·y = c con el
            rectángulo [0, x_max] × [0, y_max].

            Parámetros
            ----------
            a, b : coeficientes de x e y en la ecuación de la recta.
            c    : término independiente (rhs).
            x_max, y_max : límites del canvas.

            Retorna
            -------
            (xs, ys) : dos arrays con las coordenadas de los extremos visibles,
                        o None si la recta no atraviesa el canvas.
            """
            EPS = 1e-9
            candidatos = []

            # Borde inferior: y = 0, x ∈ [0, x_max]  →  a·x = c
            if abs(a) > EPS:
                x = c / a
                if -EPS <= x <= x_max + EPS:
                    candidatos.append((float(np.clip(x, 0, x_max)), 0.0))

            # Borde superior: y = y_max, x ∈ [0, x_max]  →  a·x = c - b·y_max
            if abs(a) > EPS:
                x = (c - b * y_max) / a
                if -EPS <= x <= x_max + EPS:
                    candidatos.append((float(np.clip(x, 0, x_max)), float(y_max)))

            # Borde izquierdo: x = 0, y ∈ [0, y_max]  →  b·y = c
            if abs(b) > EPS:
                y = c / b
                if -EPS <= y <= y_max + EPS:
                    candidatos.append((0.0, float(np.clip(y, 0, y_max))))

            # Borde derecho: x = x_max, y ∈ [0, y_max]  →  b·y = c - a·x_max
            if abs(b) > EPS:
                y = (c - a * x_max) / b
                if -EPS <= y <= y_max + EPS:
                    candidatos.append((float(x_max), float(np.clip(y, 0, y_max))))

            # Eliminar duplicados (esquinas del canvas generan candidatos iguales)
            unicos = []
            for p in candidatos:
                if not any(abs(p[0] - u[0]) < EPS and abs(p[1] - u[1]) < EPS for u in unicos):
                    unicos.append(p)

            if len(unicos) < 2:
                return None  # Recta no visible en el canvas

            # Si hay más de 2 (p. ej. pasa justo por una esquina), tomar los más
            # alejados entre sí para cubrir todo el segmento visible.
            if len(unicos) > 2:
                mejor = max(
                    ((i, j) for i in range(len(unicos)) for j in range(i + 1, len(unicos))),
                    key=lambda ij: (unicos[ij[0]][0] - unicos[ij[1]][0]) ** 2
                                    + (unicos[ij[0]][1] - unicos[ij[1]][1]) ** 2,
                )
                unicos = [unicos[mejor[0]], unicos[mejor[1]]]

            xs = np.array([unicos[0][0], unicos[1][0]])
            ys = np.array([unicos[0][1], unicos[1][1]])
            return xs, ys

        # Dibujar restricciones
        colores = ['#e6194b', '#1e88e5', '#3cb44b', '#f58231', '#911eb4', '#46f0f0', '#f032e6']
        for i, r in enumerate(restricciones):
            coefs = r.get("coeficientes", [])
            if len(coefs) < 2:
                continue

            c1 = _safe_float(coefs[0])
            c2 = _safe_float(coefs[1])
            rhs = _safe_float(r.get("rhs", 0.0))
            color = colores[i % len(colores)]

            # Descartar restricciones degeneradas (0·x1 + 0·x2 = rhs)
            if abs(c1) < 1e-9 and abs(c2) < 1e-9:
                continue

            resultado = _recta_en_canvas(c1, c2, rhs, max_x_grafico, max_y_grafico)
            if resultado is not None:
                xs, ys = resultado
                ax.plot(xs, ys, color=color, linestyle='--', label=f"R{i+1}", alpha=0.8, linewidth=1.6)

        # Dibujar función objetivo óptima (recta sólida que pasa por el óptimo)
        objetivo = problema.get("objetivo", []) or []
        if len(objetivo) >= 2 and z_opt is not None:
            c1_obj = _safe_float(objetivo[0], 0.0)
            c2_obj = _safe_float(objetivo[1], 0.0)

            # Validar que no sea recta trivial (0·x1 + 0·x2 = z_opt)
            if abs(c1_obj) > 1e-9 or abs(c2_obj) > 1e-9:
                try:
                    resultado_obj = _recta_en_canvas(
                        c1_obj, c2_obj, z_opt,
                        max_x_grafico, max_y_grafico,
                    )
                    if resultado_obj is not None:
                        xs_obj, ys_obj = resultado_obj
                        ax.plot(xs_obj, ys_obj, color='lime', linewidth=2.5, linestyle='-',
                                label=f'Z óptima = {z_opt:.2f}', alpha=0.9, zorder=5)
                except Exception:
                    pass  # Silenciosamente ignora errores en cálculo de función objetivo

        # Marcar óptimo con un círculo formal sobre la recta
        if x_opt is not None and y_opt is not None and z_opt is not None:
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
    except Exception as e:
        print(f"Error en generar_grafico_cartesiano: {e}")
        return None