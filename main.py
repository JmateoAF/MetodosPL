import flet as ft

from ui.view import MainView


def main(page: ft.Page):
    # Instanciamos la vista
    # Flet asignará automáticamente la propiedad interna .page cuando hagamos el .add()
    view = MainView(page)

    # Agregamos el componente a la página
    page.add(view)


if __name__ == "__main__":
    ft.run(main)