import flet as ft


def main(page: ft.Page):
    page.title = "Flet Moderno"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK

    page.add(
        ft.Text(
            "¡Aqui empieza todo!",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.CYAN_ACCENT  # Cambiado 'colors' por 'Colors'
        )
    )


if __name__ == "__main__":
    ft.run(main)