"""
navegador_entera.py
===================
Enrutador especializado para la familia de Programación Lineal Entera (PI).
Aísla las vistas en desarrollo para evitar colisiones de diccionarios con la arquitectura POO.
"""

import flet as ft
from src.controller.controlador_entera import ControladorEntera

ACCENT_COLOR, BG_RAIL, BG_MAIN, DIVIDER_COLOR = "#7c3aed", "#0d0f1a", "#0f1117", "#1e2130"

@ft.component
def VistaConstruccion(titulo: str):
    """Marcador de posición estático para aislar las vistas basadas en diccionarios."""
    return ft.Container(
        expand=True,
        alignment=ft.alignment.Alignment.TOP_CENTER,
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CONSTRUCTION, size=64, color="#6b7280"),
                ft.Text(f"Módulo: {titulo}", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text("Esta vista se encuentra en refactorización arquitectónica a POO puro.", size=13, color="#6b7280"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )
    )

@ft.component
def NavegadorEntera(controlador: ControladorEntera):
    selected_index, set_selected_index = ft.use_state(0)

    def on_nav_change(e: ft.ControlEvent) -> None:
        nav_rail = e.control
        indice = int(nav_rail.selected_index) 
        set_selected_index(indice)

    def create_view(index: int) -> ft.Control:
        match index:
            case 0: return VistaConstruccion("Ingreso de Parámetros Enteros")
            case 1: return VistaConstruccion("Algoritmo de Ramificación y Acotamiento")
            case _: return VistaConstruccion("Módulo PI")

    destinations = [
        ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE, label="Ingresar PI"),
        ft.NavigationRailDestination(icon=ft.Icons.ALBUM, label="Branch & Bound"),
    ]

    nav = ft.NavigationRail(
        selected_index=selected_index,
        destinations=destinations,
        on_change=on_nav_change,
        extended=False, 
        min_width=80,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=BG_RAIL, 
        indicator_color=ACCENT_COLOR,
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
