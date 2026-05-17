import flet as ft

# Main minimalista: inicializa Flet, configura tema oscuro y crea
# la instancia global del Controlador. Toda la UI está en la carpeta ui/.
from src.controller.controlador import Controlador
from ui.navegacion import NavigationApp


def main(page: ft.Page):
    page.title = "Optimizador Lineal"
    # Tema oscuro por defecto
    page.theme_mode = ft.ThemeMode.DARK
    # Aplicar color de acento (seed) tal como especifica indicaciones_gui.md
    page.theme = ft.Theme(color_scheme_seed="#4b2981")

    page.update() 

    # Instancia única y global del controlador (no crear más instancias en las vistas)
    controlador = Controlador()

    # Construir la navegación principal y montarla en la página
    nav = NavigationApp(page, controlador)
    page.add(nav.build())


if __name__ == "__main__":
    ft.run(main)
