import flet as ft

from ui.estado_ui import get_problema_activo, set_problema_activo
from ui.vista_general import VistaGeneral
from ui.vista_grafica import VistaGrafica
from ui.vista_historial import VistaHistorial
from ui.vista_ingreso import VistaIngreso
from ui.vista_ingreso_pi import VistaIngresoPi
from ui.vista_matricial import VistaMatricial
from ui.vista_bb import VistaBB


ACCENT_COLOR  = "#7c3aed"
BG_RAIL       = "#0d0f1a"
BG_MAIN       = "#0f1117"
DIVIDER_COLOR = "#1e2130"


class NavigationApp:
    """Navegación principal — rail compacto + panel central."""

    def __init__(self, page: ft.Page, controlador) -> None:
        self.page = page
        self.controlador = controlador
        self.selected_index = 0
        self.modo = "LP"  # "LP" | "PI"

        self.content_container = ft.Container(
            expand=True,
            padding=20,
            bgcolor=BG_MAIN,
        )

        self._build_nav()

    # ------------------------------------------------------------------
    # Nav rail
    # ------------------------------------------------------------------

    def _build_nav(self) -> None:
        """Reconstruye el NavigationRail según el modo activo."""
        if self.modo == "LP":
            destinations = [
                ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE,   label="Ingresar"),
                ft.NavigationRailDestination(icon=ft.Icons.HISTORY,     label="Historial"),
                ft.NavigationRailDestination(icon=ft.Icons.FLASH_ON,    label="Rápido"),
                ft.NavigationRailDestination(icon=ft.Icons.SHOW_CHART,  label="Gráfico"),
                ft.NavigationRailDestination(icon=ft.Icons.TABLE_CHART, label="Simplex"),
                ft.NavigationRailDestination(icon=ft.Icons.FUNCTIONS,   label="Gran M"),
                ft.NavigationRailDestination(icon=ft.Icons.LAYERS,      label="2 Fases"),
            ]
        else:
            destinations = [
                ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE,   label="Ingresar"),
                ft.NavigationRailDestination(icon=ft.Icons.HISTORY,     label="Historial"),
                ft.NavigationRailDestination(icon=ft.Icons.DEVICE_HUB,  label="B & B"),
            ]

        # Asegura que el índice no quede fuera de rango al cambiar modo
        if self.selected_index >= len(destinations):
            self.selected_index = 0

        self.nav = ft.NavigationRail(
            selected_index=self.selected_index,
            destinations=destinations,
            on_change=self._on_nav_change,
            extended=False,
            min_width=80,
            label_type=ft.NavigationRailLabelType.ALL,
            bgcolor=BG_RAIL,
            indicator_color=ACCENT_COLOR,
            selected_label_text_style=ft.TextStyle(color=ACCENT_COLOR, size=11),
            unselected_label_text_style=ft.TextStyle(color="#6b7280", size=11),
        )

    # ------------------------------------------------------------------
    # Cambio de modo
    # ------------------------------------------------------------------

    def cambiar_modo(self, modo: str) -> None:
        """Callback que invocan las vistas de ingreso al pulsar LP/PI."""
        if modo == self.modo:
            return
        self.modo = modo
        self.selected_index = 0
        self._build_nav()
        # Reemplaza el rail en el contenedor ya renderizado
        self._nav_container.content = self.nav
        self.show_view(0)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def _on_nav_change(self, e) -> None:
        indice = getattr(e.control, "selected_index", self.selected_index)
        self.show_view(indice)

    def show_view(self, index: int, problema: dict | None = None) -> None:
        self.selected_index = index
        self.nav.selected_index = index
        view = self._create_view(index=index, problema=problema)
        self.content_container.content = view.build()
        self.page.update()

    def show_ingreso(self, problema: dict | None = None, index: int = 0) -> None:
        if problema is not None:
            set_problema_activo(problema)
        self.show_view(index, problema=get_problema_activo())

    def _create_view(self, index: int, problema: dict | None = None):
        if self.modo == "PI":
            match index:
                case 0:
                    return VistaIngresoPi(
                        controlador=self.controlador,
                        navegar_a=self.show_view,
                        problema_inicial=problema if problema is not None else get_problema_activo(),
                        cambiar_modo=self.cambiar_modo,
                    )
                case 1:
                    return VistaHistorial(controlador=self.controlador, navegar_a=self.show_ingreso)
                case 2:
                    return VistaBB(self.controlador)
                case _:
                    return VistaIngresoPi(
                        controlador=self.controlador,
                        navegar_a=self.show_view,
                        cambiar_modo=self.cambiar_modo,
                    )
        else:
            match index:
                case 0:
                    return VistaIngreso(
                        controlador=self.controlador,
                        navegar_a=self.show_view,
                        problema_inicial=problema if problema is not None else get_problema_activo(),
                        cambiar_modo=self.cambiar_modo,
                    )
                case 1:
                    return VistaHistorial(controlador=self.controlador, navegar_a=self.show_ingreso)
                case 2:
                    return VistaGeneral(self.controlador)
                case 3:
                    return VistaGrafica(self.controlador)
                case 4:
                    return VistaMatricial(self.controlador, opcion_resolucion=2,
                        titulo="Simplex", descripcion="Iteraciones del método Simplex.")
                case 5:
                    return VistaMatricial(self.controlador, opcion_resolucion=3,
                        titulo="M Grande", descripcion="Iteraciones del método de la M Grande.")
                case 6:
                    return VistaMatricial(self.controlador, opcion_resolucion=4,
                        titulo="Dos Fases", descripcion="Iteraciones del método de Dos Fases.")
                case _:
                    return VistaIngreso(
                        controlador=self.controlador,
                        navegar_a=self.show_view,
                        cambiar_modo=self.cambiar_modo,
                    )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> ft.Control:
        self.content_container.content = self._create_view(self.selected_index).build()
        self._nav_container = ft.Container(content=self.nav, width=80, bgcolor=BG_RAIL)
        return ft.Row(
            [
                self._nav_container,
                ft.VerticalDivider(width=1, color=DIVIDER_COLOR),
                self.content_container,
            ],
            expand=True,
            spacing=0,
        )
