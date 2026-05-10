from __future__ import annotations

from fractions import Fraction
from typing import Any

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


class VistaMatricial(ft.Column):
    """Plantilla base reutilizable para métodos matriciales.

    Lee el problema activo desde el controlador (o el estado UI como respaldo),
    resuelve el LP mediante la opción indicada y renderiza las iteraciones en
    tablas dinámicas compatibles con Flet 0.84.0.
    """

    def __init__(self, controlador, opcion_resolucion: int, titulo: str, descripcion: str) -> None:
        super().__init__(expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.opcion_resolucion = opcion_resolucion
        self.titulo = titulo
        self.descripcion = descripcion

        self.status_text = ft.Text("")
        self.resultados_column = ft.Column(spacing=14)

        self.controls = [
            ft.Text(self.titulo, size=22, weight=ft.FontWeight.BOLD),
            ft.Text(self.descripcion, size=12),
            ft.Divider(color="#404040"),
            self.status_text,
            self.resultados_column,
        ]

        self.refresh()

    def _obtener_problema_activo(self) -> dict[str, Any] | None:
        problema = getattr(self.controlador, "problema_activo", None)
        if problema is None:
            problema = get_problema_activo()
        return problema

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

    def _crear_tabla(self, tabla: Any, encabezado: list) -> ft.Control:
        filas = self._normalizar_tabla(tabla)
        if not filas:
            return ft.Container(
                content=ft.Text("La tabla de esta iteración está vacía."),
                padding=12,
                border=ft.Border.all(1, ACCENT_COLOR),
                border_radius=10,
            )

        columns = [
            ft.DataColumn("Fila")
        ]
        columns.extend(
            ft.DataColumn(columna)
            for columna in encabezado
        )

        rows = []
        for indice_fila, fila in enumerate(filas):
            etiqueta = "Z/W" if indice_fila == 0 else f"R{indice_fila}"
            cells = [ft.DataCell(ft.Text(etiqueta, weight=ft.FontWeight.BOLD))]
            cells.extend(ft.DataCell(ft.Text(self._formatear_valor(valor))) for valor in fila)
            rows.append(ft.DataRow(cells=cells))

        tabla_control = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.Border.all(1, ACCENT_COLOR),
            heading_row_color=ACCENT_COLOR,
            heading_text_style=ft.TextStyle(color="white", weight=ft.FontWeight.BOLD),
            horizontal_margin=8,
            column_spacing=18,
            data_row_max_height=48,
            data_row_min_height=40,
        )

        return ft.Container(
            content=tabla_control,
            padding=12,
            border=ft.Border.all(1, ACCENT_COLOR),
            border_radius=12,
            bgcolor="#171717",
        )

    def _safe_update(self) -> None:
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def _renderizar_iteraciones(self, resultado: dict[str, Any], problema: dict[str, Any]) -> list[ft.Control]:
        controles: list[ft.Control] = []

        # Extraer datos contextuales del problema
        tipo = problema.get("tipo", "MAX")
        objetivo = problema.get("objetivo", [])
        func_objetivo = _formatear_funcion_objetivo(tipo, objetivo)

        # Renderizar resultado inicial con función objetivo
        controles.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(func_objetivo, weight=ft.FontWeight.BOLD, size=14, selectable=True),
                        ft.Text(f"Z óptimo: {self._formatear_valor(resultado.get('z_optimo', 'N/D'))}", weight=ft.FontWeight.W_600),
                        ft.Text(
                            "Variables: "
                            + ",  ".join(map(str, [f"X{i + 1} = {self._formatear_valor(v)}" for i, v in enumerate(resultado.get('variables_decision', []))]))
                        ),
                        ft.Text(f"Estado: {resultado.get('estado', 'desconocido')}", size=11, italic=True),
                        ft.Text(resultado.get('mensaje', ''), italic=True, size=11),
                    ],
                    spacing=8,
                ),
                padding=14,
                border=ft.Border.all(1, ACCENT_COLOR),
                border_radius=12,
            )
        )

        iteraciones = resultado.get("iteraciones", []) or []
        if not iteraciones:
            controles.append(
                ft.Container(
                    content=ft.Text("No se recibieron iteraciones para mostrar."),
                    padding=14,
                    border=ft.Border.all(1, ACCENT_COLOR),
                    border_radius=12,
                )
            )
            return controles

        for indice, iteracion in enumerate(iteraciones, start=1):
            fase = iteracion.get("fase")
            mensaje = iteracion.get("mensaje", "")
            cabecera = f"Iteración {indice}"
            if fase is not None:
                cabecera += f" | Fase {fase}"

            if "encabezados" in resultado:
                encabezado = resultado.get("encabezados", [])
            else:
                encabezado = resultado.get("encabezados_f1", []) if iteracion.get("fase") == 1 else resultado.get("encabezados_f2", [])

            controles.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(cabecera, size=15, weight=ft.FontWeight.BOLD),
                            ft.Text(mensaje),
                            self._crear_tabla(iteracion.get("tabla"), encabezado),
                        ],
                        spacing=10,
                    ),
                    padding=14,
                    border=ft.Border.all(1, "#404040"),
                    border_radius=12,
                )
            )

        return controles

    def refresh(self) -> None:
        problema = self._obtener_problema_activo()
        if not problema:
            self.status_text.value = "Por favor, ingresa o selecciona un problema primero."
            self.status_text.color = "#ffb74d"
            self.resultados_column.controls = [
                ft.Container(
                    content=ft.Text(
                        "No hay un problema activo disponible para resolver.",
                        italic=True,
                    ),
                    padding=16,
                    border=ft.Border.all(1, ACCENT_COLOR),
                    border_radius=12,
                )
            ]
            self._safe_update()
            return

        resultado = self.controlador.resolver_LP(problema, self.opcion_resolucion)
        if resultado is None:
            self.status_text.value = "No fue posible resolver el problema con la opción seleccionada."
            self.status_text.color = "#ff8a80"
            self.resultados_column.controls = [
                ft.Container(
                    content=ft.Text("El controlador devolvió una respuesta vacía."),
                    padding=16,
                    border=ft.Border.all(1, ACCENT_COLOR),
                    border_radius=12,
                )
            ]
            self._safe_update()
            return

        self.status_text.value = "Problema activo detectado y resuelto correctamente."
        self.status_text.color = "#7ee081"
        self.resultados_column.controls = self._renderizar_iteraciones(resultado, problema)
        self._safe_update()

    def build(self) -> ft.Control:
        return self
