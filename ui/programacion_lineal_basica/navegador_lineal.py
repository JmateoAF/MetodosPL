"""
navegador_lineal.py
===================
Enrutador especializado para la familia de Programación Lineal Continua.
"""

import flet as ft
from src.controller.controlador_lineal import ControladorLineal

# Importaciones de vistas refactorizadas
from ui.vista_general import VistaGeneral
from ui.vista_grafica import VistaGrafica
from ui.vista_historial import VistaHistorial
from ui.vista_ingreso import VistaIngreso
from ui.vista_matricial import VistaMatricial

ACCENT_COLOR, BG_RAIL, BG_MAIN, DIVIDER_COLOR = "#7c3aed", "#0d0f1a", "#0f1117", "#1e2130"

class NavegadorLineal:
    def __init__(self, page: ft.Page, controlador: ControladorLineal) -> None:
        self.page = page
        self.controlador = controlador
        self.selected_index = 0

        self.content_container = ft.Container(expand=True, padding=20, bgcolor=BG_MAIN)
        self.destinations = [
            ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE, label="Ingresar"),
            ft.NavigationRailDestination(icon=ft.Icons.HISTORY, label="Historial"),
            ft.NavigationRailDestination(icon=ft.Icons.FLASH_ON, label="Rápido"),
            ft.NavigationRailDestination(icon=ft.Icons.SHOW_CHART, label="Gráfico"),
            ft.NavigationRailDestination(icon=ft.Icons.TABLE_CHART, label="Simplex"),
            ft.NavigationRailDestination(icon=ft.Icons.FUNCTIONS, label="Gran M"),
            ft.NavigationRailDestination(icon=ft.Icons.LAYERS, label="2 Fases"),
        ]

        self.nav = ft.NavigationRail(
            selected_index=self.selected_index,
            destinations=self.destinations,
            on_change=self._on_nav_change,
            extended=False, min_width=80,
            label_type=ft.NavigationRailLabelType.ALL,
            bgcolor=BG_RAIL, indicator_color=ACCENT_COLOR,
            selected_label_text_style=ft.TextStyle(color=ACCENT_COLOR, size=11),
            unselected_label_text_style=ft.TextStyle(color="#6b7280", size=11),
        )

    def _on_nav_change(self, e: ft.ControlEvent) -> None:
        self.show_view(int(e.control.selected_index))

    def show_view(self, index: int) -> None:
        self.selected_index = index
        self.nav.selected_index = index
        self.content_container.content = self._create_view(index).build()
        self.page.update()

    def show_ingreso(self, index: int = 0) -> None:
        self.show_view(index)

    def _create_view(self, index: int):
        match index:
            case 0: return VistaIngreso(self.controlador, self.show_view)
            case 1: return VistaHistorial(self.controlador, self.show_ingreso)
            case 2: return VistaGeneral(self.controlador)
            case 3: return VistaGrafica(self.controlador)
            case 4: return VistaMatricial(self.controlador, 2, "Simplex", "Iteraciones del método Simplex.")
            case 5: return VistaMatricial(self.controlador, 3, "M Grande", "Iteraciones del método de la M Grande.")
            case 6: return VistaMatricial(self.controlador, 4, "Dos Fases", "Iteraciones del método de Dos Fases.")
            case _: return VistaIngreso(self.controlador, self.show_view)

    def build(self) -> ft.Row:
        self.content_container.content = self._create_view(self.selected_index).build()
        return ft.Row(
            [ft.Container(content=self.nav, width=80, bgcolor=BG_RAIL), ft.VerticalDivider(width=1, color=DIVIDER_COLOR), self.content_container],
            expand=True, spacing=0
        )
