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


def _stat_card(titulo: str, valor: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Text(titulo, size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
            ft.Text(valor, size=18, color=color, weight=ft.FontWeight.BOLD),
        ], spacing=4),
        padding=16,
        border_radius=10,
        bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
        expand=True,
    )


class VistaGeneral(ft.Column):
    def __init__(self, controlador) -> None:
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.status_row = ft.Row([], visible=False)
        self.resultado_container = ft.Column(spacing=12)

        self.controls = [
            ft.Column([
                ft.Text("Solución Rápida", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Resultado óptimo sin pasos intermedios.", size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.resultado_container,
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
            self.resultado_container.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CALCULATE, color=TEXT_MUTED, size=48),
                        ft.Text("Sin problema activo", color=TEXT_MUTED, size=14,
                                text_align=ft.TextAlign.CENTER),
                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=48, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)), alignment=ft.alignment.Alignment(0, 0),
                )
            ]
            self._safe_update()
            return

        resultado = self.controlador.resolver_LP(problema, 1)

        if not resultado or resultado.get("estado") != 0:
            mensaje = resultado.get("mensaje", "Error desconocido") if resultado else "Respuesta vacía."
            self._set_status(f"No se encontró solución óptima.", AMBER)
            self.resultado_container.controls = [
                ft.Container(
                    content=ft.Text(mensaje, color=AMBER, text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.W_500),
                    padding=20, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"), left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44")),
                )
            ]
            self._safe_update()
            return

        self._set_status("Problema resuelto correctamente.", GREEN)

        tipo = problema.get("tipo", "MAX")
        objetivo = problema.get("objetivo", [])
        fo_str = _formatear_fo(tipo, objetivo)
        z_val = _formatear_valor(resultado.get("valor_z", "N/D"))
        variables = resultado.get("variables", []) or []
        mensaje = resultado.get("mensaje", "")

        # Cards de stats
        stat_cards = ft.Row([
            _stat_card("Z óptimo", z_val, GREEN),
            _stat_card("Variables", str(len(variables)), BLUE),
            _stat_card("Restricciones", str(len(problema.get("restricciones", []))), AMBER),
        ], spacing=10)

        # Variables detalle
        vars_detail = ft.Container(
            content=ft.Column([
                ft.Text("Valores óptimos", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"X{i+1}", size=11, color=TEXT_MUTED),
                            ft.Text(_formatear_valor(v), size=16, color=TEXT_PRIMARY,
                                    weight=ft.FontWeight.BOLD),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=16,
                        border_radius=8, bgcolor="#1e2130",
                        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                    )
                    for i, v in enumerate(variables)
                ], wrap=True, spacing=8),
            ], spacing=10),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
        )

        # Función objetivo + mensaje
        fo_card = ft.Container(
            content=ft.Column([
                ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                ft.Text(mensaje, size=11, color=TEXT_MUTED, italic=True) if mensaje else ft.Container(),
            ], spacing=6),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
        )

        self.resultado_container.controls = [fo_card, stat_cards, vars_detail]
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def build(self) -> ft.Control:
        return self
