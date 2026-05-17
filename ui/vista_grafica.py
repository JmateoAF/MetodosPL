from __future__ import annotations

import flet as ft

from ui.estado_ui import get_problema_activo


ACCENT_COLOR = "#7c3aed"
BG_CARD      = "#161822"
BORDER_COLOR = "#2a2d3a"
TEXT_MUTED   = "#6b7280"
TEXT_PRIMARY = "#f0f0f0"
GREEN        = "#7dd3a8"
AMBER        = "#f6ad55"
RED          = "#ef645f"
BLUE         = "#63b3ed"


def _formatear_fo(tipo: str, objetivo: list) -> str:
    if not objetivo:
        return f"{tipo} Z = 0"
    terminos = []
    for i, coef in enumerate(objetivo):
        try:
            c = float(coef)
        except Exception:
            c = 0.0
        if c == 0:
            continue
        var = f"X{i+1}"
        if c > 0:
            terminos.append(f"{'+ ' if terminos else ''}{c:.4g}{var}" if abs(c) != 1 else f"{'+ ' if terminos else ''}{var}")
        else:
            terminos.append(f"- {abs(c):.4g}{var}" if abs(c) != 1 else f"- {var}")
    return f"{tipo} Z = {' '.join(terminos) or '0'}"


def _formatear_valor(valor) -> str:
    from fractions import Fraction
    if hasattr(valor, "item"):
        valor = valor.item()
    if isinstance(valor, Fraction):
        return str(valor)
    if isinstance(valor, float):
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")
        return texto if texto else "0"
    return str(valor)


class VistaGrafica(ft.Column):
    def __init__(self, controlador) -> None:
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador

        self.status_row = ft.Row([], visible=False)
        self.img_container = ft.Container(
            alignment=ft.alignment.Alignment(0, 0),
            padding=16,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            border_radius=12,
            bgcolor=BG_CARD,
            expand=True,
        )
        self.resultado_container = ft.Column(spacing=10)

        self.controls = [
            ft.Column([
                ft.Text("Método Gráfico", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Región factible para problemas de exactamente 2 variables.", size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.resultado_container,
            self.img_container,
        ]
        self.refresh()

    def _set_status(self, mensaje: str, color: str, icono=None) -> None:
        if icono is None:
            icono = ft.Icons.CHECK_CIRCLE if color == GREEN else ft.Icons.WARNING_AMBER
        self.status_row.visible = True
        self.status_row.controls = [
            ft.Container(
                content=ft.Row([ft.Icon(icono, color=color, size=15),
                                ft.Text(mensaje, color=color, size=12)], spacing=8),
                padding=14,
                border_radius=8, bgcolor=color + "18", border=ft.Border(top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"), left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44")),
            )
        ]

    def refresh(self) -> None:
        problema = getattr(self.controlador, "problema_activo", None) or get_problema_activo()

        if not problema:
            self._set_status("Ingresa o selecciona un problema primero.", AMBER, ft.Icons.INFO_OUTLINE)
            self.img_container.content = ft.Column([
                ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_MUTED, size=48),
                ft.Text("Sin problema activo", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.resultado_container.controls = []
            self._safe_update()
            return

        objetivo = problema.get("objetivo", []) or []
        num_vars = len(objetivo)

        if num_vars != 2:
            self._set_status(
                f"El método gráfico requiere exactamente 2 variables ({num_vars} detectadas).", RED
            )
            self.img_container.content = ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=RED, size=40),
                ft.Text(f"Este problema tiene {num_vars} variables.\nEl método gráfico solo aplica para 2.",
                        color=RED, text_align=ft.TextAlign.CENTER, size=13),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.resultado_container.controls = []
            self._safe_update()
            return

        resultado = self.controlador.resolver_LP(problema, 1)
        if not resultado:
            self._set_status("Error al resolver el problema.", RED)
            self.img_container.content = ft.Text("Error de resolución.", color=RED)
            self.resultado_container.controls = []
            self._safe_update()
            return

        estado = resultado.get("estado")
        if estado == 0:
            self._set_status("Gráfico generado correctamente.", GREEN)
            self._generar_grafico(problema, resultado)
        else:
            mensaje_error = resultado.get("mensaje", "El problema no tiene solución óptima acotada.")
            self._set_status(f"Atención: {mensaje_error}", AMBER)
            self.img_container.content = ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER, color=AMBER, size=40),
                ft.Text(mensaje_error, color=AMBER, text_align=ft.TextAlign.CENTER, size=13),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self._renderizar_resultados(problema, resultado)

        self._safe_update()

    def _generar_grafico(self, problema: dict, resultado: dict) -> None:
        try:
            from src.utils.graficador import generar_grafico_cartesiano
            img_b64 = generar_grafico_cartesiano(problema, resultado)
            if img_b64:
                self.img_container.content = ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN)
            else:
                self.img_container.content = ft.Text("Error al generar gráfico.", color=RED)
            self._renderizar_resultados(problema, resultado)
        except Exception as e:
            self.img_container.content = ft.Container(
                content=ft.Text(f"Error: {str(e)[:100]}", color=RED, size=10),
                padding=14, border_radius=12, border=ft.Border(top=ft.BorderSide(1, RED), bottom=ft.BorderSide(1, RED), left=ft.BorderSide(1, RED), right=ft.BorderSide(1, RED)),
            )
            self.resultado_container.controls = []

    def _renderizar_resultados(self, problema: dict, resultado: dict) -> None:
        tipo = problema.get("tipo", "MAX")
        objetivo = problema.get("objetivo", [])
        fo_str = _formatear_fo(tipo, objetivo)
        z_val = _formatear_valor(resultado.get("valor_z", "N/D"))
        variables = resultado.get("variables", []) or []
        mensaje = resultado.get("mensaje", "")

        self.resultado_container.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text(fo_str, size=13, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Z óptimo", size=10, color=TEXT_MUTED),
                                ft.Text(z_val, size=16, color=GREEN, weight=ft.FontWeight.BOLD),
                            ], spacing=2),
                            padding=14,
                            border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        ),
                        *[
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(f"X{i+1}", size=10, color=TEXT_MUTED),
                                    ft.Text(_formatear_valor(v), size=16, color=TEXT_PRIMARY,
                                            weight=ft.FontWeight.BOLD),
                                ], spacing=2),
                                padding=14,
                                border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                            )
                            for i, v in enumerate(variables)
                        ],
                    ], wrap=True, spacing=8),
                    ft.Text(mensaje, size=11, color=TEXT_MUTED, italic=True) if mensaje else ft.Container(),
                ], spacing=10),
                padding=16, border_radius=12, bgcolor=BG_CARD,
                border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
            )
        ]

    def _safe_update(self) -> None:
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def build(self) -> ft.Control:
        return self
