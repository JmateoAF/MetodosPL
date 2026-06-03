from __future__ import annotations
from copy import deepcopy
from fractions import Fraction
import flet as ft
from ui.estado_ui import set_problema_activo

ACCENT_COLOR = "#7c3aed"
BG_CARD      = "#161822"
BG_FIELD     = "#1e2130"
BORDER_COLOR = "#2a2d3a"
TEXT_MUTED   = "#6b7280"
TEXT_PRIMARY = "#f0f0f0"
GREEN        = "#1d9e75"
AMBER        = "#f6ad55"
RED          = "#ef645f"


def _campo(label: str, valor="") -> ft.TextField:
    return ft.TextField(
        label=label,
        value="" if valor is None else str(valor),
        width=90,
        text_align=ft.TextAlign.CENTER,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        cursor_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
        keyboard_type=ft.KeyboardType.TEXT,
        hint_text="0",
        border_radius=8,
    )


def _btn(texto: str, icono, on_click, color=None) -> ft.ElevatedButton:
    bg = color or ACCENT_COLOR
    return ft.ElevatedButton(
        content=ft.Row(
            [ft.Icon(icono, size=15, color="white"), ft.Text(texto, size=12, color="white")],
            tight=True, spacing=6,
        ),
        bgcolor=bg,
        on_click=on_click,
    )


def _seccion(titulo: str, contenido: ft.Control) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Text(titulo, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            contenido,
        ], spacing=12),
        padding=16,
        border_radius=12,
        bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER_COLOR),
            bottom=ft.BorderSide(1, BORDER_COLOR),
            left=ft.BorderSide(1, BORDER_COLOR),
            right=ft.BorderSide(1, BORDER_COLOR),
        ),
    )


def _nuevo_check(indice: int, valor: bool = True) -> ft.Checkbox:
    return ft.Checkbox(
        label=f"X{indice + 1} ∈ ℤ",
        value=valor,
        active_color=ACCENT_COLOR,
    )


class VistaIngresoPi(ft.Container):
    def __init__(
        self,
        controlador,
        navegar_a=None,
        problema_inicial: dict | None = None,
        cambiar_modo=None,          # callback a NavigationApp.cambiar_modo
    ) -> None:
        super().__init__(expand=True, padding=0, bgcolor="transparent")
        self.controlador = controlador
        self.navegar_a = navegar_a
        self.cambiar_modo_cb = cambiar_modo
        self.problema_inicial = deepcopy(problema_inicial) if problema_inicial else None

        self.tipo_dropdown = ft.Dropdown(
            label="Optimización",
            value=(self.problema_inicial or {}).get("tipo", "MAX"),
            options=[ft.dropdown.Option("MAX"), ft.dropdown.Option("MIN")],
            width=160,
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            border_radius=8,
        )

        self.status_text = ft.Text("", size=12, visible=False)
        self.objective_fields: list[ft.TextField] = []
        self.restriction_rows: list[dict] = []
        self.integer_checks: list[ft.Checkbox] = []    # uno por variable
        self._build_initial_form()
        self.content = self._build_layout()

    # ------------------------------------------------------------------
    # Toggle de modo LP / PI
    # ------------------------------------------------------------------

    def _build_mode_toggle(self) -> ft.Container:
        def _modo_btn(texto: str, activo: bool, on_click) -> ft.ElevatedButton:
            return ft.ElevatedButton(
                content=ft.Text(texto, size=11, color="white"),
                bgcolor=ACCENT_COLOR if activo else "#374151",
                on_click=on_click,
            )

        return ft.Container(
            content=ft.Row([
                ft.Text("Modo:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                _modo_btn(
                    "Programación Lineal", activo=False,
                    on_click=lambda _e: self.cambiar_modo_cb("LP") if self.cambiar_modo_cb else None,
                ),
                _modo_btn(
                    "Programación Lineal Entera", activo=True,
                    on_click=lambda _e: None,           # ya está en PI
                ),
            ], spacing=8),
            padding=10,
            border_radius=8,
            bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, "#374151"),
                bottom=ft.BorderSide(1, "#374151"),
                left=ft.BorderSide(1, "#374151"),
                right=ft.BorderSide(1, "#374151"),
            ),
        )

    # ------------------------------------------------------------------
    # Formulario inicial
    # ------------------------------------------------------------------

    def _build_initial_form(self) -> None:
        objetivo = list((self.problema_inicial or {}).get("objetivo", []) or [])
        restricciones = list((self.problema_inicial or {}).get("restricciones", []) or [])
        enteras = list((self.problema_inicial or {}).get("enteras", []) or [])
        num_variables = max(len(objetivo), 2)
        num_restricciones = max(len(restricciones), 1)

        for i in range(num_variables):
            valor = objetivo[i] if i < len(objetivo) else ""
            self.objective_fields.append(_campo(f"X{i+1}", valor))
            es_entera = bool(enteras[i]) if i < len(enteras) else True
            self.integer_checks.append(_nuevo_check(i, es_entera))

        for i in range(num_restricciones):
            r = restricciones[i] if i < len(restricciones) else {}
            self.restriction_rows.append(self._crear_fila_restriccion(i, r))

    def _crear_fila_restriccion(self, indice: int, restriccion: dict | None = None) -> dict:
        restriccion = restriccion or {}
        coeficientes = list(restriccion.get("coeficientes", []) or [])
        signo = restriccion.get("signo", "<=")
        rhs = restriccion.get("rhs", "")
        coeff_fields = []
        for vi in range(len(self.objective_fields)):
            valor = coeficientes[vi] if vi < len(coeficientes) else ""
            coeff_fields.append(_campo(f"X{vi+1}", valor))
        return {
            "indice": indice,
            "coeficientes": coeff_fields,
            "signo": ft.Dropdown(
                value=signo,
                options=[ft.dropdown.Option("<="), ft.dropdown.Option(">="), ft.dropdown.Option("==")],
                width=90,
                border_color=BORDER_COLOR,
                focused_border_color=ACCENT_COLOR,
                bgcolor=BG_FIELD,
                color=TEXT_PRIMARY,
                border_radius=8,
            ),
            "rhs": _campo("RHS", rhs),
        }

    def _parse_numeric(self, value):
        texto = "" if value is None else str(value).strip().replace(",", ".")
        if texto == "":
            return 0
        try:
            if "/" in texto:
                return Fraction(texto)
            if any(s in texto.lower() for s in (".", "e")):
                return float(texto)
            return int(texto)
        except Exception:
            try:
                return float(texto)
            except Exception:
                return 0

    # ------------------------------------------------------------------
    # Sección de variables enteras
    # ------------------------------------------------------------------

    def _build_integer_section(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FUNCTIONS, size=14, color=ACCENT_COLOR),
                    ft.Text("Variables enteras", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ], spacing=6),
                ft.Text(
                    "Marca las variables que deben tomar valores enteros.",
                    size=11, color=TEXT_MUTED,
                ),
                ft.Row(self.integer_checks, wrap=False, spacing=16),
            ], spacing=10),
            padding=16,
            border_radius=12,
            bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, "#374151"),
                bottom=ft.BorderSide(1, "#374151"),
                left=ft.BorderSide(1, "#374151"),
                right=ft.BorderSide(1, "#374151"),
            ),
        )

    # ------------------------------------------------------------------
    # Layout principal
    # ------------------------------------------------------------------

    def _build_layout(self) -> ft.Control:
        # Función objetivo
        fo_controls = [ft.Text("Z =", color=TEXT_MUTED, size=13)]
        for i, campo in enumerate(self.objective_fields):
            fo_controls.append(campo)
            if i < len(self.objective_fields) - 1:
                fo_controls.append(ft.Text("+", color=TEXT_MUTED, size=14))

        fo_section = _seccion(
            "Función objetivo",
            ft.Column([
                self.tipo_dropdown,
                ft.Row(fo_controls, wrap=True, spacing=6),
                ft.Row([
                    _btn("Añadir variable", ft.Icons.ADD, self._agregar_variable),
                    _btn("Eliminar variable", ft.Icons.REMOVE, self._eliminar_variable, color="#374151"),
                ], spacing=8, wrap=True),
            ], spacing=10),
        )

        # Restricciones
        restricciones_col = ft.Column(spacing=10)
        for i, fila in enumerate(self.restriction_rows, start=1):
            restricciones_col.controls.append(self._build_restriction_row(i, fila))
        restricciones_col.controls.append(
            ft.Row([
                _btn("Añadir restricción", ft.Icons.ADD_CIRCLE_OUTLINE, self._agregar_restriccion),
                _btn("Eliminar restricción", ft.Icons.REMOVE_CIRCLE_OUTLINE, self._eliminar_restriccion, color="#374151"),
            ], spacing=8, wrap=True),
        )
        rest_section = _seccion("Restricciones", restricciones_col)

        return ft.Container(
            content=ft.Column([
                # ── Toggle de modo ──────────────────────────────────
                self._build_mode_toggle(),
                # ── Encabezado ──────────────────────────────────────
                ft.Column([
                    ft.Text("Ingresar Problema", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("Define función objetivo, variables enteras y restricciones.", size=12, color=TEXT_MUTED),
                ], spacing=2),
                ft.Divider(color=BORDER_COLOR, height=1),
                fo_section,
                self._build_integer_section(),  # ← sección exclusiva PI
                rest_section,
                ft.Row([
                    _btn("Guardar problema", ft.Icons.SAVE, self._guardar_problema, color=GREEN),
                    _btn("Restaurar valores", ft.Icons.REFRESH, self._restaurar_valores, color="#374151"),
                    _btn("Restaurar problema", ft.Icons.UNDO, self._restaurar_problema, color="#374151"),
                    _btn("Restablecer", ft.Icons.RESTART_ALT, self._restablecer_problema, color="#374151"),
                ], spacing=8, wrap=True),
                self.status_text,
            ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True,
        )

    def _build_restriction_row(self, indice: int, fila: dict) -> ft.Container:
        campos = []
        for i, campo in enumerate(fila["coeficientes"]):
            campos.append(campo)
            if i < len(fila["coeficientes"]) - 1:
                campos.append(ft.Text("+", color=TEXT_MUTED, size=12))

        return ft.Container(
            content=ft.Column([
                ft.Text(f"Restricción {indice}", size=12, weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
                ft.Row(campos + [fila["signo"], fila["rhs"]], wrap=True, spacing=6),
            ], spacing=8),
            padding=12,
            border_radius=10,
            bgcolor="#12141f",
            border=ft.Border(
                top=ft.BorderSide(1, "#252836"),
                bottom=ft.BorderSide(1, "#252836"),
                left=ft.BorderSide(1, "#252836"),
                right=ft.BorderSide(1, "#252836"),
            ),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, mensaje: str, color: str) -> None:
        self.status_text.value = mensaje
        self.status_text.color = color
        self.status_text.visible = True

    def _rebuild_content(self) -> None:
        self.content = self._build_layout()
        self.update()

    # ------------------------------------------------------------------
    # Acciones de variables y restricciones
    # ------------------------------------------------------------------

    def _agregar_variable(self, _e) -> None:
        i = len(self.objective_fields)
        self.objective_fields.append(_campo(f"X{i+1}"))
        for fila in self.restriction_rows:
            fila["coeficientes"].append(_campo(f"X{i+1}"))
        self.integer_checks.append(_nuevo_check(i, True))
        self._rebuild_content()

    def _eliminar_variable(self, _e) -> None:
        if len(self.objective_fields) > 1:
            self.objective_fields.pop()
            for fila in self.restriction_rows:
                if fila["coeficientes"]:
                    fila["coeficientes"].pop()
            if self.integer_checks:
                self.integer_checks.pop()
            self._rebuild_content()
        else:
            self._set_status("No puedes eliminar la última variable.", RED)
            self.update()

    def _agregar_restriccion(self, _e) -> None:
        self.restriction_rows.append(self._crear_fila_restriccion(len(self.restriction_rows)))
        self._rebuild_content()

    def _eliminar_restriccion(self, _e) -> None:
        if len(self.restriction_rows) > 1:
            self.restriction_rows.pop()
            self._rebuild_content()
        else:
            self._set_status("No puedes eliminar la última restricción.", RED)
            self.update()

    def _restaurar_valores(self, _e) -> None:
        for campo in self.objective_fields:
            campo.value = ""
        for fila in self.restriction_rows:
            for campo in fila["coeficientes"]:
                campo.value = ""
            fila["rhs"].value = ""
        self._set_status("Valores vaciados.", AMBER)
        self.update()

    def _restaurar_problema(self, _e) -> None:
        self.objective_fields = []
        self.restriction_rows = []
        self.integer_checks = []
        self._build_initial_form()
        self._rebuild_content()

    def _restablecer_problema(self, _e) -> None:
        self.objective_fields = []
        self.restriction_rows = []
        self.integer_checks = []
        self.tipo_dropdown.value = "MAX"
        for i in range(2):
            self.objective_fields.append(_campo(f"X{i+1}"))
            self.integer_checks.append(_nuevo_check(i, True))
        self.restriction_rows.append(self._crear_fila_restriccion(0))
        self._rebuild_content()

    # ------------------------------------------------------------------
    # Guardar
    # ------------------------------------------------------------------

    def _armar_diccionario_entrada(self) -> dict:
        return {
            "tipo": self.tipo_dropdown.value or "MAX",
            "objetivo": [self._parse_numeric(c.value) for c in self.objective_fields],
            "restricciones": [
                {
                    "coeficientes": [self._parse_numeric(c.value) for c in fila["coeficientes"]],
                    "signo": fila["signo"].value or "<=",
                    "rhs": self._parse_numeric(fila["rhs"].value),
                }
                for fila in self.restriction_rows
            ],
            "enteras": [bool(chk.value) for chk in self.integer_checks],
        }

    def _guardar_problema(self, _e) -> None:
        datos = self._armar_diccionario_entrada()
        resultado = self.controlador.operar_problema(datos, 1)
        set_problema_activo(datos)
        setattr(self.controlador, "problema_activo", deepcopy(datos))
        if resultado is not None:
            self._set_status("✓ Problema guardado y establecido como activo.", GREEN)
        else:
            self._set_status("✗ No fue posible guardar el problema.", RED)
        self.update()

    def build(self) -> ft.Control:
        return self
