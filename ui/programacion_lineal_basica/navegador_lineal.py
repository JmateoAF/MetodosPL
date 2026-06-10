"""
navegador_lineal.py
===================
Enrutador especializado para la familia de Programación Lineal Continua.
"""

import flet as ft
from src.controller.controlador_lineal import ControladorLineal

# Importaciones de vistas refactorizadas
from ui.programacion_lineal_basica.vista_general import VistaGeneral
from ui.programacion_lineal_basica.vista_grafica import VistaGrafica
from ui.programacion_lineal_basica.vista_historial import VistaHistorial
from ui.programacion_lineal_basica.vista_ingreso import VistaIngreso
from ui.programacion_lineal_basica.vista_matricial import VistaMatricial

ACCENT_COLOR, BG_RAIL, BG_MAIN, DIVIDER_COLOR = "#7c3aed", "#0d0f1a", "#0f1117", "#1e2130"

@ft.component
def NavegadorLineal(controlador: ControladorLineal):
    selected_index, set_selected_index = ft.use_state(0)

    # Callback to show views
    def show_view(index: int) -> None:
        set_selected_index(index)

    # Use use_ref to cache VistaIngreso so its fields aren't wiped out on tab changes
    vista_ingreso_ref = ft.use_ref(None)
    if vista_ingreso_ref.current is None:
        vista_ingreso_ref.current = VistaIngreso(controlador, show_view)

    def on_nav_change(e: ft.ControlEvent) -> None:
        nav_rail = e.control
        indice = int(nav_rail.selected_index) 
        show_view(indice)

    def create_view(index: int) -> ft.Control:
        match index:
            case 0: return vista_ingreso_ref.current
            case 1: return VistaHistorial(controlador, show_view)
            case 2: return VistaGeneral(controlador)
            case 3: return VistaGrafica(controlador)
            case 4: return VistaMatricial(controlador, 2, "Simplex", "Iteraciones del método Simplex.")
            case 5: return VistaMatricial(controlador, 3, "M Grande", "Iteraciones del método de la M Grande.")
            case 6: return VistaMatricial(controlador, 4, "Dos Fases", "Iteraciones del método de Dos Fases.")
            case _: return vista_ingreso_ref.current

    destinations = [
        ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE, label="Ingresar"),
        ft.NavigationRailDestination(icon=ft.Icons.HISTORY, label="Historial"),
        ft.NavigationRailDestination(icon=ft.Icons.ANALYTICS, label="Vista General"),
        ft.NavigationRailDestination(icon=ft.Icons.SHOW_CHART, label="Gráfica"),
        ft.NavigationRailDestination(icon=ft.Icons.TABLE_ROWS, label="Simplex"),
        ft.NavigationRailDestination(icon=ft.Icons.FUNCTIONS, label="M Grande"),
        ft.NavigationRailDestination(icon=ft.Icons.LAYERS, label="Dos Fases"),
    ]

    nav = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        extended=False,
        bgcolor=BG_RAIL,
        indicator_color=ACCENT_COLOR,
        destinations=destinations,
        on_change=on_nav_change,
        selected_label_text_style=ft.TextStyle(color=ACCENT_COLOR, size=11),
        unselected_label_text_style=ft.TextStyle(color="#6b7280", size=11),
    )

    return ft.Row(
        controls=[
            nav,
            ft.VerticalDivider(width=1, color=DIVIDER_COLOR),
            ft.Container(
                content=create_view(selected_index),
                expand=True,
                padding=20,
                bgcolor=BG_MAIN
            ),
        ],
        spacing=0,
        expand=True,
    )
