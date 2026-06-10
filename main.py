import flet as ft

# Importación de la Fachada y el Enrutador Maestro
from src.controller.controlador_principal import ControladorPrincipal
from ui.navegador_principal import NavegadorPrincipal

def main(page: ft.Page):
    page.title = "Optimizador Lineal MVC"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="#4b2981")

    # Instancia única de la Fachada que administrará a todos los sub-controladores
    controlador_fachada = ControladorPrincipal()

    # Arranque declarativo: delegamos el renderizado al componente NavegadorPrincipal
    # sin necesidad de pasar 'page' ni usar page.add() o page.update()
    page.render(lambda: NavegadorPrincipal(controlador_fachada))

if __name__ == "__main__":
    ft.run(main)