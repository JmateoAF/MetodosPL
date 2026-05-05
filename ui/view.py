import flet as ft


class MainView(ft.Column):
    def __init__(self, page_ref: ft.Page):
        super().__init__()
        self.main_page = page_ref

        # Configuración básica
        self.main_page.title = "Software IO"
        self.main_page.theme_mode = ft.ThemeMode.DARK

        self.texto_bienvenida = ft.Text(
            value="Bienvenido al Sistema",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.CYAN_ACCENT
        )

        # CAMBIO AQUÍ: En lugar de text="Púlsame", usamos content o simplemente el valor directo
        self.boton_accion = ft.ElevatedButton(
            content=ft.Text("Púlsame"),  # Esta es la forma más segura en versiones nuevas
            on_click=self.handle_click
        )

        self.controls = [
            self.texto_bienvenida,
            self.boton_accion
        ]
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def handle_click(self, e):
        self.texto_bienvenida.value = "¡Funcionando perfectamente!"
        self.texto_bienvenida.color = ft.Colors.GREEN_ACCENT
        self.update()