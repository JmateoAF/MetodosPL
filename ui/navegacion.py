import flet as ft

from ui.estado_ui import get_problema_activo, set_problema_activo
from ui.vista_general import VistaGeneral
from ui.vista_grafica import VistaGrafica
from ui.vista_historial import VistaHistorial
from ui.vista_ingreso import VistaIngreso
from ui.vista_matricial import VistaMatricial


ACCENT_COLOR = "#4b2981"


class NavigationApp:
    """Navegación principal de la aplicación.

    Orquesta el NavigationRail lateral y carga las vistas en el panel central.
    Mantiene la instancia única del controlador y comunica a las vistas cómo
    navegar entre pantallas sin tocar la capa `src/`.
    """

    def __init__(self, page: ft.Page, controlador) -> None:
        self.page = page
        self.controlador = controlador
        self.selected_index = 0

        self.content_container = ft.Container(expand=True, padding=20)

        self.destinations = [
            ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE, label="Ingresar Problema"),
            ft.NavigationRailDestination(icon=ft.Icons.HISTORY, label="Historial de Problemas"),
            ft.NavigationRailDestination(icon=ft.Icons.FLASH_ON, label="Solución Rápida"),
            ft.NavigationRailDestination(icon=ft.Icons.SHOW_CHART, label="Método Gráfico"),
            ft.NavigationRailDestination(icon=ft.Icons.TABLE_CHART, label="Simplex"),
            ft.NavigationRailDestination(icon=ft.Icons.FUNCTIONS, label="M Grande"),
            ft.NavigationRailDestination(icon=ft.Icons.LAYERS, label="Dos Fases"),
        ]

        self.nav = ft.NavigationRail(
            selected_index=self.selected_index,
            destinations=self.destinations,
            on_change=lambda e: self._on_nav_change(e),
            extended=False,
            label_type=ft.NavigationRailLabelType.ALL,
            indicator_color=ACCENT_COLOR,
            selected_label_text_style=ft.TextStyle(color=ACCENT_COLOR),
            unselected_label_text_style=ft.TextStyle(color="#d0d0d0"),
        )

    def _on_nav_change(self, e) -> None:
        indice = getattr(e.control, "selected_index", self.selected_index)
        self.show_view(indice)

    def show_view(self, index: int, problema: dict | None = None) -> None:
        self.selected_index = index
        self.nav.selected_index = index

        view = self._create_view(index=index, problema=problema)
        # Limpiar y reemplazar explícitamente el contenido del panel central.
        self.content_container.content = None
        self.content_container.content = view.build()
        self.page.update()

    def show_ingreso(self, problema: dict | None = None, index: int = 0) -> None:
        if problema is not None:
            set_problema_activo(problema)
        self.show_view(index, problema=get_problema_activo())

    def _create_view(self, index: int, problema: dict | None = None):
        match index:
            case 0:
                return VistaIngreso(
                    controlador=self.controlador,
                    navegar_a=self.show_view,
                    problema_inicial=problema if problema is not None else get_problema_activo(),
                )
            case 1:
                return VistaHistorial(
                    controlador=self.controlador,
                    navegar_a=self.show_ingreso,
                )
            case 2:
                return VistaGeneral(self.controlador)
            case 3:
                return VistaGrafica(self.controlador)
            case 4:
                return VistaMatricial(
                    self.controlador,
                    opcion_resolucion=2,
                    titulo="Simplex",
                    descripcion="Renderizado matricial de las iteraciones del método Simplex.",
                )
            case 5:
                return VistaMatricial(
                    self.controlador,
                    opcion_resolucion=3,
                    titulo="M Grande",
                    descripcion="Renderizado matricial de las iteraciones del método de la M Grande.",
                )
            case 6:
                return VistaMatricial(
                    self.controlador,
                    opcion_resolucion=4,
                    titulo="Dos Fases",
                    descripcion="Renderizado matricial de las iteraciones del método de Dos Fases.",
                )
            case _:
                return VistaIngreso(controlador=self.controlador, navegar_a=self.show_view)

    def build(self) -> ft.Control:
        # Cargar vista inicial sin forzar update prematuro.
        self.content_container.content = self._create_view(self.selected_index).build()
        return ft.Row(
            [
                ft.Container(content=self.nav, width=280, padding=10),
                ft.VerticalDivider(width=1, color="#404040"),
                self.content_container,
            ],
            expand=True,
        )