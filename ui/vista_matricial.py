from __future__ import annotations

from fractions import Fraction
from typing import Any

import flet as ft

from ui.estado_ui import get_problema_activo


ACCENT_COLOR = "#7c3aed"
BG_CARD      = "#161822"
BG_TABLE     = "#0d0f1a"
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


class VistaMatricial(ft.Column):
    def __init__(self, controlador, opcion_resolucion: int, titulo: str, descripcion: str) -> None:
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.opcion_resolucion = opcion_resolucion
        self.titulo = titulo
        self.descripcion = descripcion

        self.status_row = ft.Row([], visible=False)
        self.resultados_column = ft.Column(spacing=14)

        self.controls = [
            ft.Column([
                ft.Text(self.titulo, size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text(self.descripcion, size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.resultados_column,
        ]
        self.refresh()

    def _formatear_valor(self, valor: Any) -> str:
        if hasattr(valor, "item"):
            valor = valor.item()
        if isinstance(valor, Fraction):
            return str(valor)
        if isinstance(valor, float):
            texto = f"{valor:.6f}".rstrip("0").rstrip(".")
            return texto if texto else "0"
        return str(valor)

    def _normalizar_tabla(self, tabla: Any) -> list[list[Any]]:
        if hasattr(tabla, "tolist"):
            tabla = tabla.tolist()
        return [list(fila) for fila in tabla or []]

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

    def _crear_tabla(self, tabla: Any, encabezado: list) -> ft.Control:
        filas = self._normalizar_tabla(tabla)
        if not filas:
            return ft.Container(
                content=ft.Text("Tabla vacía.", color=TEXT_MUTED, italic=True),
                padding=12, border_radius=10, bgcolor=BG_CARD,
                border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            )

        columns = [
            ft.DataColumn(ft.Text("Fila", weight=ft.FontWeight.BOLD, size=12, color="white")),
        ] + [
            ft.DataColumn(ft.Text(str(col), weight=ft.FontWeight.BOLD, size=12, color="white"))
            for col in encabezado
        ]

        rows = []
        for idx, fila in enumerate(filas):
            etiqueta = "Z/W" if idx == 0 else f"R{idx}"
            es_z = idx == 0
            cell_color = ACCENT_COLOR + "33" if es_z else None
            cells = [
                ft.DataCell(ft.Text(etiqueta, weight=ft.FontWeight.BOLD, size=12,
                                    color=BLUE if es_z else GREEN))
            ]
            cells += [
                ft.DataCell(ft.Text(self._formatear_valor(v), size=12, color=TEXT_PRIMARY))
                for v in fila
            ]
            rows.append(ft.DataRow(
                cells=cells,
                color={"": cell_color} if cell_color else {"": BG_TABLE}, # Si no es Z, le mete el color oscuro de la tabla
            ))

        tabla_control = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "55"), bottom=ft.BorderSide(1, ACCENT_COLOR + "55"), left=ft.BorderSide(1, ACCENT_COLOR + "55"), right=ft.BorderSide(1, ACCENT_COLOR + "55")),
            heading_row_color={"": ACCENT_COLOR},
            data_row_color={"": BG_TABLE}, 
            heading_row_height=42,
            data_row_max_height=44,
            data_row_min_height=40,
            horizontal_margin=12,
            column_spacing=20,
            divider_thickness=0.5,
        )

        return ft.Container(
            content=ft.Row([tabla_control], scroll=ft.ScrollMode.AUTO),
            padding=12,
            border_radius=10,
            bgcolor=BG_TABLE,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
        )

    def _renderizar_iteraciones(self, resultado: dict, problema: dict) -> list[ft.Control]:
        controles: list[ft.Control] = []

        tipo = problema.get("tipo", "MAX")
        objetivo = problema.get("objetivo", [])
        fo_str = _formatear_fo(tipo, objetivo)

        variables = resultado.get("variables_decision") or []
        z_val = self._formatear_valor(resultado.get("z_optimo", "N/D"))
        estado = resultado.get("estado", "")
        mensaje = resultado.get("mensaje", "")

        texto_vars = ", ".join(f"X{i+1} = {self._formatear_valor(v)}" for i, v in enumerate(variables)) \
            if variables else "N/D"

        # Tarjeta resumen superior
        controles.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Z óptimo", size=10, color=TEXT_MUTED),
                                ft.Text(z_val, size=18, color=GREEN, weight=ft.FontWeight.BOLD),
                            ], spacing=2),
                            padding=16,
                            border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Variables", size=10, color=TEXT_MUTED),
                                ft.Text(texto_vars, size=13, color=TEXT_PRIMARY),
                            ], spacing=2),
                            padding=16,
                            border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        ),
                    ], spacing=8, wrap=True),
                    ft.Text(f"Estado: {estado}", size=11, color=TEXT_MUTED, italic=True) if estado else ft.Container(),
                    ft.Text(mensaje, size=11, color=TEXT_MUTED, italic=True) if mensaje else ft.Container(),
                ], spacing=10),
                padding=16, border_radius=12, bgcolor=BG_CARD,
                border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
            )
        )

        iteraciones = resultado.get("iteraciones", []) or []
        if not iteraciones:
            return controles

        for idx, iteracion in enumerate(iteraciones, start=1):
            fase = iteracion.get("fase")
            msg_iter = iteracion.get("mensaje", "")

            # Título de iteración con badge de fase
            titulo_row = ft.Row([
                ft.Text(f"Iteración {idx}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                *(
                    [ft.Container(
                        content=ft.Text(f"Fase {fase}", size=10, color="white", weight=ft.FontWeight.W_600),
                        padding=8,
                        bgcolor=GREEN.replace("#7dd3a8", "#1d9e75") if fase == 1 else BLUE.replace("#63b3ed", "#2563eb"),
                        border_radius=99,
                    )] if fase is not None else []
                ),
            ], spacing=8)

            if "encabezados" in resultado:
                encabezado = resultado.get("encabezados", [])
            else:
                encabezado = resultado.get("encabezados_f1", []) if iteracion.get("fase") == 1 \
                    else resultado.get("encabezados_f2", [])

            controles.append(
                ft.Container(
                    content=ft.Column([
                        titulo_row,
                        ft.Text(msg_iter, size=12, color=TEXT_MUTED) if msg_iter else ft.Container(),
                        self._crear_tabla(iteracion.get("tabla"), encabezado),
                    ], spacing=10),
                    padding=16, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                )
            )

        return controles

    def _safe_update(self) -> None:
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def refresh(self) -> None:
        self.resultados_column.controls.clear()
        problema = getattr(self.controlador, "problema_activo", None) or get_problema_activo()

        if not problema:
            self._set_status("Ingresa o selecciona un problema primero.", AMBER, ft.Icons.INFO_OUTLINE)
            self.resultados_column.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.TABLE_CHART, color=TEXT_MUTED, size=48),
                        ft.Text("Sin problema activo", color=TEXT_MUTED, size=13,
                                text_align=ft.TextAlign.CENTER),
                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=48, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)), alignment=ft.alignment.Alignment(0, 0),
                )
            ]
            self._safe_update()
            return

        resultado = self.controlador.resolver_LP(problema, self.opcion_resolucion)
        if resultado is None:
            self._set_status("El controlador devolvió respuesta vacía.", RED)
            self.resultados_column.controls = [
                ft.Container(
                    content=ft.Text("No se pudo resolver el problema.", color=RED),
                    padding=16, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"), left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44")),
                )
            ]
            self._safe_update()
            return

        estado = resultado.get("estado", "")
        if estado == "optimo":
            self._set_status("Problema resuelto correctamente.", GREEN)
        elif estado == "requiere_otro_metodo":
            self._set_status("Este problema requiere otro método (restricciones >= o ==).", AMBER)
        else:
            self._set_status(f"Atención: estado → {estado}", AMBER)

        self.resultados_column.controls = self._renderizar_iteraciones(resultado, problema)
        self._safe_update()

    def build(self) -> ft.Control:
        return self