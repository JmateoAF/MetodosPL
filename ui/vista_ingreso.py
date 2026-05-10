from __future__ import annotations

from copy import deepcopy
from fractions import Fraction

import flet as ft

from ui.estado_ui import set_problema_activo


ACCENT_COLOR = "#4b2981"


class VistaIngreso(ft.Container):
    """Vista de ingreso de datos y CRUD de la Fase 2.

    No usa `ft.UserControl`. Hereda directamente de `ft.Container` y mantiene
    el formulario dinámico para construir el diccionario de entrada exigido por
    la arquitectura MVC del proyecto.
    """

    def __init__(self, controlador, navegar_a=None, problema_inicial: dict | None = None) -> None:
        super().__init__(expand=True, padding=0)
        self.controlador = controlador
        self.navegar_a = navegar_a
        self.problema_inicial = deepcopy(problema_inicial) if problema_inicial else None

        self.tipo_dropdown = ft.Dropdown(
            label="Tipo de objetivo",
            value=(self.problema_inicial or {}).get("tipo", "MAX"),
            options=[
                ft.dropdown.Option("MAX"),
                ft.dropdown.Option("MIN"),
            ],
            width=220,
            border_color="#404040",
            focused_border_color=ACCENT_COLOR,
        )

        self.status_text = ft.Text("", size=12)
        self.objective_fields: list[ft.TextField] = []
        self.restriction_rows: list[dict] = []

        self._build_initial_form()
        self.content = self._build_layout()

    def _build_initial_form(self) -> None:
        objetivo = list((self.problema_inicial or {}).get("objetivo", []) or [])
        restricciones = list((self.problema_inicial or {}).get("restricciones", []) or [])

        num_variables = max(len(objetivo), 2)
        num_restricciones = max(len(restricciones), 1)

        for indice in range(num_variables):
            valor = objetivo[indice] if indice < len(objetivo) else ""
            self.objective_fields.append(self._crear_campo_coeficiente(indice, valor))

        for indice in range(num_restricciones):
            restriccion = restricciones[indice] if indice < len(restricciones) else {}
            self.restriction_rows.append(self._crear_fila_restriccion(indice, restriccion))

    def _crear_campo_coeficiente(self, indice: int, valor="") -> ft.TextField:
        return ft.TextField(
            label=f"X{indice + 1}",
            value="" if valor is None else str(valor),
            width=110,
            text_align=ft.TextAlign.RIGHT,
            border_color="#404040",
            focused_border_color=ACCENT_COLOR,
            cursor_color=ACCENT_COLOR,
            keyboard_type=ft.KeyboardType.TEXT,
            hint_text="0",
        )

    def _crear_fila_restriccion(self, indice: int, restriccion: dict | None = None) -> dict:
        restriccion = restriccion or {}
        coeficientes = list(restriccion.get("coeficientes", []) or [])
        signo = restriccion.get("signo", "<=")
        rhs = restriccion.get("rhs", "")

        coeff_fields: list[ft.TextField] = []
        for var_index in range(len(self.objective_fields)):
            valor = coeficientes[var_index] if var_index < len(coeficientes) else ""
            coeff_fields.append(self._crear_campo_coeficiente(var_index, valor))

        return {
            "indice": indice,
            "coeficientes": coeff_fields,
            "signo": ft.Dropdown(
                value=signo,
                options=[
                    ft.dropdown.Option("<="),
                    ft.dropdown.Option(">="),
                    ft.dropdown.Option("=="),
                ],
                width=110,
                border_color="#404040",
                focused_border_color=ACCENT_COLOR,
            ),
            "rhs": ft.TextField(
                label="RHS",
                value="" if rhs is None else str(rhs),
                width=110,
                text_align=ft.TextAlign.RIGHT,
                border_color="#404040",
                focused_border_color=ACCENT_COLOR,
                cursor_color=ACCENT_COLOR,
                keyboard_type=ft.KeyboardType.TEXT,
                hint_text="0",
            ),
        }

    def _parse_numeric(self, value):
        texto = "" if value is None else str(value).strip()
        if texto == "":
            return 0

        texto = texto.replace(",", ".")
        try:
            if "/" in texto:
                return Fraction(texto)
            if any(separador in texto.lower() for separador in (".", "e")):
                return float(texto)
            return int(texto)
        except Exception:
            try:
                return float(texto)
            except Exception:
                return 0

    def _build_layout(self) -> ft.Control:
        header = ft.Text("Ingresar Problema", size=22, weight=ft.FontWeight.BOLD)
        subtitle = ft.Text(
            "Sección para el ingreso y carga de los ejercicios de programación lineal.",
            size=12,
        )

        objective_row = ft.Row(self.objective_fields, wrap=True, spacing=10)
        objective_section = self._section_card(
            "Función objetivo",
            ft.Column(
                [
                    ft.Row([ft.Text("Z =", weight=ft.FontWeight.BOLD), objective_row], wrap=True, spacing=12),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "➕ Añadir variable",
                                icon="add",
                                bgcolor=ACCENT_COLOR,
                                color="white",
                                on_click=self._agregar_variable,
                            ),
                            ft.ElevatedButton(
                                "🗑 Eliminar variable",
                                icon="delete_outline",
                                bgcolor=ACCENT_COLOR, #"#ff6b6b",
                                color="white",
                                on_click=self._eliminar_variable,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=12,
            ),
        )

        restricciones_controls: list[ft.Control] = []
        for indice, fila in enumerate(self.restriction_rows, start=1):
            restricciones_controls.append(self._build_restriction_row(indice, fila))

        restricciones_controls.append(
            ft.Row(
                [
                    ft.ElevatedButton(
                        "➕ Añadir restricción",
                        icon="add_circle",
                        bgcolor=ACCENT_COLOR,
                        color="white",
                        on_click=self._agregar_restriccion,
                    ),
                    ft.ElevatedButton(
                        "🗑 Eliminar restricción",
                        icon="delete",
                        bgcolor=ACCENT_COLOR, #"#ff6b6b",
                        color="white",
                        on_click=self._eliminar_restriccion,
                    ),
                ],
                spacing=8,
            )
        )

        restrictions_section = self._section_card(
            "Restricciones",
            ft.Column(restricciones_controls, spacing=12),
        )

        save_button = ft.ElevatedButton(
            "Guardar Problema",
            icon="save",
            bgcolor=ACCENT_COLOR,
            color="white",
            on_click=self._guardar_problema,
        )

        restore_values_button = ft.ElevatedButton(
            "🔄 Restaurar valores",
            icon="refresh",
            bgcolor=ACCENT_COLOR, #"#ffb74d",
            color="white",
            on_click=self._restaurar_valores,
        )

        restore_problem_button = ft.ElevatedButton(
            "⟲ Restaurar problema",
            icon="reset_tv",
            bgcolor=ACCENT_COLOR, #"#7ee081",
            color="white",
            on_click=self._restaurar_problema,
        )

        reset_to_base_button = ft.ElevatedButton(
            "🔁 Restablecer problema",
            icon="restart_alt",
            bgcolor=ACCENT_COLOR, #"#ff9800",
            color="white",
            on_click=self._restablecer_problema,
        )

        return ft.Container(
            content=ft.Column(
                [
                    header,
                    subtitle,
                    ft.Divider(color="#404040"),
                    ft.Row([self.tipo_dropdown], spacing=12),
                    objective_section,
                    restrictions_section,
                    ft.Row(
                        [save_button, restore_values_button, restore_problem_button, reset_to_base_button],
                        spacing=8,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    self.status_text,
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
        )

    def _section_card(self, title: str, content: ft.Control) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                    content,
                ],
                spacing=12,
            ),
            padding=16,
            border_radius=12,
            border=ft.Border.all(1, "#404040"),
        )

    def _build_restriction_row(self, indice: int, fila: dict) -> ft.Control:
        coeff_fields = fila["coeficientes"]
        coeff_wrap = ft.Row(coeff_fields, wrap=True, spacing=10)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Restricción {indice}", weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            coeff_wrap,
                            fila["signo"],
                            fila["rhs"],
                        ],
                        wrap=True,
                        spacing=12,
                    ),
                ],
                spacing=10,
            ),
            padding=12,
            border_radius=10,
            border=ft.Border.all(1, "#303030"),
        )

    def _rebuild_content(self) -> None:
        self.content = self._build_layout()
        self.update()

    def _agregar_variable(self, _event) -> None:
        indice = len(self.objective_fields)
        self.objective_fields.append(self._crear_campo_coeficiente(indice))

        for fila in self.restriction_rows:
            fila["coeficientes"].append(self._crear_campo_coeficiente(indice))

        self._rebuild_content()

    def _agregar_restriccion(self, _event) -> None:
        self.restriction_rows.append(self._crear_fila_restriccion(len(self.restriction_rows), None))
        self._rebuild_content()

    def _eliminar_variable(self, _event) -> None:
        """Elimina la última variable del objetivo y de todas las restricciones."""
        if len(self.objective_fields) > 1:
            self.objective_fields.pop()
            for fila in self.restriction_rows:
                if fila["coeficientes"]:
                    fila["coeficientes"].pop()
            self._rebuild_content()
            self.status_text.value = "Variable eliminada."
            self.status_text.color = "#ffb74d"
        else:
            self.status_text.value = "No puedes eliminar la última variable."
            self.status_text.color = "#ff8a80"
        self.update()

    def _eliminar_restriccion(self, _event) -> None:
        """Elimina la última restricción."""
        if len(self.restriction_rows) > 1:
            self.restriction_rows.pop()
            self._rebuild_content()
            self.status_text.value = "Restricción eliminada."
            self.status_text.color = "#ffb74d"
        else:
            self.status_text.value = "No puedes eliminar la última restricción."
            self.status_text.color = "#ff8a80"
        self.update()

    def _restaurar_valores(self, _event) -> None:
        """Limpia todas las celdas de entrada (restaura valores vacíos)."""
        for campo in self.objective_fields:
            campo.value = ""
        for fila in self.restriction_rows:
            for campo in fila["coeficientes"]:
                campo.value = ""
            fila["rhs"].value = ""
        self.status_text.value = "Valores restaurados (vaciados)."
        self.status_text.color = "#ffb74d"
        self.update()

    def _restaurar_problema(self, _event) -> None:
        """Restaura el problema al estado inicial."""
        self.objective_fields = []
        self.restriction_rows = []
        self._build_initial_form()
        self._rebuild_content()
        self.status_text.value = "Problema restaurado al estado inicial."
        self.status_text.color = "#7ee081"

    def _restablecer_problema(self, _event) -> None:
        """Restablece el problema al estado base (1 variable, 1 restricción, vacío)."""
        self.objective_fields = []
        self.restriction_rows = []
        self.tipo_dropdown.value = "MAX"
        
        # Agregar 1 variable vacía
        self.objective_fields.append(self._crear_campo_coeficiente(0, ""))
        
        # Agregar 1 restricción vacía
        self.restriction_rows.append(self._crear_fila_restriccion(0, None))
        
        self._rebuild_content()
        self.status_text.value = "Problema restablecido al estado base."
        self.status_text.color = "#ff9800"
        self.update()

    def _armar_diccionario_entrada(self) -> dict:
        datos_entrada = {
            "tipo": self.tipo_dropdown.value or "MAX",
            "objetivo": [self._parse_numeric(campo.value) for campo in self.objective_fields],
            "restricciones": [],
        }

        for fila in self.restriction_rows:
            datos_entrada["restricciones"].append(
                {
                    "coeficientes": [self._parse_numeric(campo.value) for campo in fila["coeficientes"]],
                    "signo": fila["signo"].value or "<=",
                    "rhs": self._parse_numeric(fila["rhs"].value),
                }
            )

        return datos_entrada

    def _guardar_problema(self, _event) -> None:
        datos_entrada = self._armar_diccionario_entrada()
        resultado = self.controlador.operar_problema(datos_entrada, 1)
        set_problema_activo(datos_entrada)
        setattr(self.controlador, "problema_activo", deepcopy(datos_entrada))

        if resultado is not None:
            self.status_text.value = "Problema guardado correctamente y establecido como problema activo."
            self.status_text.color = "#7ee081"
        else:
            self.status_text.value = "No fue posible guardar el problema."
            self.status_text.color = "#ff8a80"

        self.update()

    def build(self) -> ft.Control:
        return self

