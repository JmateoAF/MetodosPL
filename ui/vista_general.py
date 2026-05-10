from __future__ import annotations

import flet as ft

from ui.estado_ui import get_problema_activo


ACCENT_COLOR = "#4b2981"


def _formatear_funcion_objetivo(tipo: str, objetivo: list) -> str:
    """Formatea la función objetivo como 'MAX Z = 2X1 + 3X2 - X3'."""
    if not objetivo:
        return f"{tipo} Z = 0"

    terminos = []
    for i, coef in enumerate(objetivo):
        try:
            c = float(coef)
        except (TypeError, ValueError):
            c = 0.0

        if c == 0:
            continue

        var_name = f"X{i + 1}"
        if c > 0:
            if not terminos:
                terminos.append(f"{c:.4g}{var_name}" if c != 1 else var_name)
            else:
                terminos.append(f"+ {c:.4g}{var_name}" if c != 1 else f"+ {var_name}")
        else:
            terminos.append(f"- {abs(c):.4g}{var_name}" if abs(c) != 1 else f"- {var_name}")

    expr = " ".join(terminos) if terminos else "0"
    return f"{tipo} Z = {expr}"


def _formatear_valor(valor) -> str:
    """Formatea un valor para presentación."""
    from fractions import Fraction

    if hasattr(valor, "item"):
        valor = valor.item()

    if isinstance(valor, Fraction):
        return str(valor)

    if isinstance(valor, float):
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")
        return texto if texto else "0"

    return str(valor)


class VistaGeneral(ft.Column):
    """
    Vista de Solución Rápida - Presenta resultados sin gráfico
    """

    def __init__(self, controlador) -> None:
        super().__init__(expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador

        self.status_text = ft.Text("", size=12)
        self.resultado_container = ft.Column(spacing=10)

        self.controls = [
            ft.Text("Solución Rápida (Análisis General)", size=22, weight=ft.FontWeight.BOLD),
            ft.Divider(color="#404040"),
            self.status_text,
            self.resultado_container,
        ]

        self.refresh()

    def refresh(self) -> None:
        """Obtiene el problema activo y lo resuelve."""
        problema = getattr(self.controlador, "problema_activo", None) or get_problema_activo()

        if not problema:
            self.status_text.value = "Por favor, ingresa o selecciona un problema primero."
            self.status_text.color = "#ffb74d"
            self.resultado_container.controls = [
                ft.Container(
                    content=ft.Text("No hay un problema activo disponible.", italic=True),
                    padding=14,
                    border=ft.Border.all(1, ACCENT_COLOR),
                    border_radius=12,
                )
            ]
            self._safe_update()
            return

        resultado = self.controlador.resolver_LP(problema, 1)
        if not resultado or resultado.get("estado") != 0:
            self.status_text.value = f"No se pudo resolver: {resultado.get('mensaje', 'Error desconocido') if resultado else 'Error'}"
            self.status_text.color = "#ff8a80"
            self.resultado_container.controls = []
            self._safe_update()
            return

        self.status_text.value = "Problema resuelto correctamente."
        self.status_text.color = "#7ee081"

        # Renderizar resultado formateado como en vista_matricial
        tipo = problema.get("tipo", "MAX")
        objetivo = problema.get("objetivo", [])
        func_objetivo = _formatear_funcion_objetivo(tipo, objetivo)

        z_optimo = _formatear_valor(resultado.get("valor_z", "N/D"))
        variables = resultado.get("variables", []) or []
        mensaje = resultado.get("mensaje", "")

        self.resultado_container.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text(func_objetivo, weight=ft.FontWeight.BOLD, size=14, selectable=True),
                    ft.Text(f"Z óptimo: {z_optimo}", weight=ft.FontWeight.W_600),
                    ft.Text(
                        "Variables: "
                        + ",  ".join([f"X{i + 1} = {_formatear_valor(v)}" for i, v in enumerate(variables)])
                    ),
                    ft.Text(mensaje, italic=True, size=11),
                ], spacing=8),
                padding=14,
                border=ft.Border.all(1, ACCENT_COLOR),
                border_radius=12,
            )
        ]

        self._safe_update()


    def _safe_update(self) -> None:
        """Actualiza la vista de forma segura."""
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def build(self) -> ft.Control:
        return self