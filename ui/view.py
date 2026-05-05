import flet as ft


class MainView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__()
        self.main_page = page_ref

        # Configuración de la ventana
        self.main_page.title = "Solver de Programación Lineal 2026"
        self.main_page.theme_mode = ft.ThemeMode.DARK
        self.main_page.padding = 20

        # Títulos
        self.titulo = ft.Text(
            "Programación Lineal",
            size=40,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.CYAN_ACCENT
        )

        self.subtitulo = ft.Text(
            "Selecciona un método para comenzar",
            size=16,
            color=ft.Colors.BLUE_GREY_200
        )

        # Contenedor de opciones con wrap=True
        self.menu_opciones = ft.Row(
            wrap=True,
            spacing=20,
            run_spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self._crear_item_menu("Método Gráfico", ft.Icons.AUTO_GRAPH, "/grafico"),
                self._crear_item_menu("Simplex", ft.Icons.GRID_ON, "/simplex"),
                self._crear_item_menu("M Grande", ft.Icons.PLUS_ONE, "/mgrande"),
                self._crear_item_menu("Dos Fases", ft.Icons.STAIRS, "/dosfases"),
                self._crear_item_menu("Resolver", ft.Icons.PLAY_ARROW_ROUNDED, "/auto"),
            ]
        )

        # Estructura principal
        self.controls = [
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.titulo,
                    self.subtitulo,
                    ft.Container(height=30),
                    self.menu_opciones
                ]
            )
        ]
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def _crear_item_menu(self, nombre: str, icono_code: str, ruta: str):
        """Crea un botón de estilo tarjeta sin usar parámetros obsoletos"""
        return ft.Container(
            content=ft.Column(
                [
                    # CAMBIO CLAVE: Quitamos 'name=' y pasamos el icono directo
                    ft.Icon(icono_code, size=35, color=ft.Colors.CYAN_ACCENT),
                    ft.Text(nombre, size=14, weight=ft.FontWeight.W_600),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=140,
            height=140,
            bgcolor=ft.Colors.SURFACE_VARIANT,  # Cambiado a un color sólido por si la opacidad falla
            border_radius=20,
            ink=True,
            on_click=lambda _: self._navegar(ruta),
        )

    def _navegar(self, ruta: str):
        print(f"Navegando hacia: {ruta}")