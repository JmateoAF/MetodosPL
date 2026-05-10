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


def generar_grafico_barras(nombres_vars: list, valores_vars: list) -> str:
    """Genera gráfico de barras con valores de variables."""
    try:
        fig, ax = plt.subplots(figsize=(8, 5), facecolor='#1e1e1e')
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_color('white')

        # Convertir valores a float
        valores_float = [_safe_float(v, 0.0) for v in valores_vars]

        ax.bar(nombres_vars, valores_float, color='#4b2981', edgecolor='white', linewidth=1.5)
        ax.set_title("Variables de Decisión", color='white', fontsize=14, fontweight='bold')
        ax.set_ylabel("Valor", color='white')
        ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

        plt.tight_layout()
        return _fig_to_base64(fig)
    except Exception as e:
        print(f"Error en generar_grafico_barras: {e}")
        return None


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

            # Validar división por cero
            if abs(c1) < 1e-9 and abs(c2) < 1e-9:
                continue

            if abs(c2) < 1e-9 and c1 != 0:  # Vertical
                x_val = rhs / c1
                ax.axvline(x_val, color=color, linestyle='--', label=f"R{i+1}", alpha=0.8)
            elif abs(c1) < 1e-9 and c2 != 0:  # Horizontal
                y_val = rhs / c2
                ax.axhline(y_val, color=color, linestyle='--', label=f"R{i+1}", alpha=0.8)
            else:  # Recta general
                x_vals = np.array([0, rhs / c1 if c1 != 0 else 0])
                y_vals = np.array([rhs / c2 if c2 != 0 else 0, 0])
                ax.plot(x_vals, y_vals, color=color, linestyle='--', label=f"R{i+1}", alpha=0.8)

        # Dibujar función objetivo óptima (recta sólida que pasa por el óptimo)
        objetivo = problema.get("objetivo", []) or []
        if len(objetivo) >= 2 and z_opt is not None:
            c1_obj = _safe_float(objetivo[0], 0.0)
            c2_obj = _safe_float(objetivo[1], 0.0)
            
            # Validar que no sea recta trivial
            if abs(c1_obj) > 1e-9 or abs(c2_obj) > 1e-9:
                try:
                    # Calcular interceptos: c1*X1 + c2*X2 = z_opt
                    x_intercept = z_opt / c1_obj if abs(c1_obj) > 1e-9 else None
                    y_intercept = z_opt / c2_obj if abs(c2_obj) > 1e-9 else None
                    
                    # Construir puntos para la recta
                    obj_x = []
                    obj_y = []
                    
                    if x_intercept is not None and x_intercept >= 0:
                        obj_x.append(x_intercept)
                        obj_y.append(0)
                    if y_intercept is not None and y_intercept >= 0:
                        obj_x.append(0)
                        obj_y.append(y_intercept)
                    
                    # Si no hay interceptos válidos, usar el rango del gráfico
                    if len(obj_x) < 2:
                        if abs(c2_obj) > 1e-9:  # Resolver para X1 en los límites de Y
                            y_test = [0, max_y_grafico]
                            for y_val in y_test:
                                x_val = (z_opt - c2_obj * y_val) / c1_obj if abs(c1_obj) > 1e-9 else 0
                                if 0 <= x_val <= max_x_grafico:
                                    obj_x.append(x_val)
                                    obj_y.append(y_val)
                        elif abs(c1_obj) > 1e-9:  # Resolver para X2 en los límites de X
                            x_test = [0, max_x_grafico]
                            for x_val in x_test:
                                y_val = (z_opt - c1_obj * x_val) / c2_obj if abs(c2_obj) > 1e-9 else 0
                                if 0 <= y_val <= max_y_grafico:
                                    obj_x.append(x_val)
                                    obj_y.append(y_val)
                    
                    # Dibujar si hay al menos 2 puntos
                    if len(obj_x) >= 2:
                        ax.plot(obj_x[:2], obj_y[:2], color='lime', linewidth=2.5, linestyle='-',
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
