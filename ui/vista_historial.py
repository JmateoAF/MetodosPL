from __future__ import annotations

from copy import deepcopy

import flet as ft

from ui.estado_ui import get_problema_activo, set_problema_activo


ACCENT_COLOR = "#7c3aed"
BG_CARD      = "#161822"
BG_MAIN      = "#0f1117"
BORDER_COLOR = "#2a2d3a"
TEXT_MUTED   = "#6b7280"
TEXT_PRIMARY = "#f0f0f0"
GREEN        = "#7dd3a8"
AMBER        = "#f6ad55"
RED          = "#ef645f"


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


def _badge(texto: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(texto, size=10, color="white", weight=ft.FontWeight.W_600),
        padding=10,
        bgcolor=color,
        border_radius=99,
    )


def _btn(texto: str, icono, on_click, color=ACCENT_COLOR) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        content=ft.Row(
            [ft.Icon(icono, size=15, color="white"), ft.Text(texto, size=11, color="white")],
            spacing=5, tight=True,
        ),
        bgcolor=color,
        on_click=on_click,
    )


class VistaHistorial(ft.Column):
    def __init__(self, controlador, navegar_a=None) -> None:
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.navegar_a = navegar_a

        self.cards_column = ft.Column(spacing=10, expand=True)
        self.status_row = ft.Row([], visible=False)

        self.controls = [
            ft.Column([
                ft.Text("Historial de Problemas", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Consulta, carga, clona/edita o elimina problemas guardados.", size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.cards_column,
        ]
        self.refresh()

    def _formatear_restricciones(self, restricciones: list) -> str:
        partes = []
        for r in restricciones[:3]:
            coefs = r.get("coeficientes", [])
            signo = r.get("signo", "<=")
            rhs = r.get("rhs", 0)
            terminos = " + ".join(f"{c:.4g}X{i+1}" for i, c in enumerate(coefs) if c != 0)
            partes.append(f"{terminos} {signo} {rhs}")
        if len(restricciones) > 3:
            partes.append(f"... y {len(restricciones)-3} más")
        return "\n".join(partes)

    def _crear_tarjeta(self, indice: int, problema: dict) -> ft.Control:
        snapshot = deepcopy(problema)
        tipo = snapshot.get("tipo", "MAX")
        objetivo = snapshot.get("objetivo", [])
        restricciones = snapshot.get("restricciones", [])
        fo_str = _formatear_fo(tipo, objetivo)
        num_vars = len(objetivo)
        badge_color = "#1d9e75" if tipo == "MAX" else "#2563eb"

        return ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Row([
                        ft.Text(f"Problema #{indice+1}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        _badge(tipo, badge_color),
                        _badge(f"{num_vars} var{'s' if num_vars != 1 else ''}", "#374151"),
                        _badge(f"{len(restricciones)} rest.", "#374151"),
                    ], spacing=8),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                # Función objetivo formateada
                ft.Container(
                    content=ft.Text(fo_str, size=13, color=TEXT_PRIMARY, weight=ft.FontWeight.W_500,
                                    selectable=True),
                    padding=12,
                    bgcolor="#1e2130",
                    border_radius=8,
                    border=ft.Border(top=ft.BorderSide(1, "#2a2d3a"), bottom=ft.BorderSide(1, "#2a2d3a"), left=ft.BorderSide(1, "#2a2d3a"), right=ft.BorderSide(1, "#2a2d3a")),
                ),

                # Restricciones preview
                ft.Text(
                    self._formatear_restricciones(restricciones),
                    size=11, color=TEXT_MUTED,
                ),

                # Acciones
                ft.Row([
                    _btn("Cargar", ft.Icons.UPLOAD, lambda _e, s=snapshot: self._cargar_problema(s)),
                    _btn("Clonar y Editar", ft.Icons.CONTENT_COPY,
                         lambda _e, s=snapshot: self._clonar_y_editar(s), color="#374151"),
                    _btn("Eliminar", ft.Icons.DELETE_OUTLINE,
                         lambda _e, idx=indice: self._eliminar_problema(idx), color="#7f1d1d"),
                ], spacing=8, wrap=True),
            ], spacing=10),
            padding=16,
            border_radius=12,
            bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
        )

    def refresh(self) -> None:
        historial = self.controlador.obtener_historial_de_problema() or []
        if not historial:
            self.cards_column.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, color=TEXT_MUTED, size=40),
                        ft.Text("No hay problemas guardados.", color=TEXT_MUTED, size=13,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("Guarda un problema desde la vista de ingreso.",
                                color="#4a4f66", size=11, text_align=ft.TextAlign.CENTER),
                    ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    border_radius=12,
                    bgcolor=BG_CARD,
                    border=ft.Border(
                        top=ft.BorderSide(1, BORDER_COLOR),
                        bottom=ft.BorderSide(1, BORDER_COLOR),
                        left=ft.BorderSide(1, BORDER_COLOR),
                        right=ft.BorderSide(1, BORDER_COLOR)
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                )
            ]
        else:
            self.cards_column.controls = [
                self._crear_tarjeta(i, p) for i, p in enumerate(historial)
            ]

    def _set_status(self, mensaje: str, color: str) -> None:
        icono = ft.Icons.CHECK_CIRCLE if color == GREEN else (
            ft.Icons.DELETE if color == RED else ft.Icons.INFO
        )
        self.status_row.visible = True
        self.status_row.controls = [
            ft.Container(
                content=ft.Row([ft.Icon(icono, color=color, size=15),
                                ft.Text(mensaje, color=color, size=12)], spacing=8),
                padding=14,
                border_radius=8,
                bgcolor=color + "18",
                border=ft.Border(top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"), left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44")),
            )
        ]

    def _cargar_problema(self, problema: dict) -> None:
        set_problema_activo(problema)
        setattr(self.controlador, "problema_activo", deepcopy(problema))
        self._set_status("Problema cargado como activo.", GREEN)
        if self.navegar_a:
            self.navegar_a(deepcopy(problema), 2)
        else:
            self.update()

    def _clonar_y_editar(self, problema: dict) -> None:
        set_problema_activo(problema)
        setattr(self.controlador, "problema_activo", deepcopy(problema))
        self._set_status("Problema clonado. Edítalo en la vista de ingreso.", AMBER)
        if self.navegar_a:
            self.navegar_a(deepcopy(problema))
        else:
            self.update()

    def _eliminar_problema(self, indice: int) -> None:
        eliminado = self.controlador.operar_problema(None, 3, indice)
        if eliminado is not None and get_problema_activo() == eliminado:
            set_problema_activo(None)
            setattr(self.controlador, "problema_activo", None)
        self.refresh()
        self._set_status("Problema eliminado del historial.", RED)
        self.update()

    def build(self) -> ft.Control:
        self.refresh()
        return self
