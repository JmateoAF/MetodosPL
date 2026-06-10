# ui/vista_ingreso_pi.py
"""
vista_ingreso_pi.py
===================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Implementa un entorno flexible de entrada de datos para modelos de PL Entera (PI).
"""

from __future__ import annotations
from copy import deepcopy
from fractions import Fraction
from typing import Optional
import flet as ft
from src.controller.controlador_entera import ControladorEntera

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


def _nuevo_tipo_dropdown(indice: int, valor: str = "Entera", on_select=None) -> ft.Dropdown:
    """Dropdown de tipo por variable: Continua / Entera / Binaria."""
    return ft.Dropdown(
        label=f"X{indice + 1}",
        value=valor,
        options=[
            ft.dropdown.Option("Entera"),
            ft.dropdown.Option("Binaria"),
        ],
        width=120,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        border_radius=8,
        on_select=on_select,
    )


@ft.component
def VistaIngresoPi(
    controlador: ControladorEntera,
    navegar_a=None,
    problema_inicial: dict | None = None,
    cambiar_modo=None,
):
    status_text_val, set_status_text_val = ft.use_state(("", "")) # (message, color)
    refresh_trigger, set_refresh_trigger = ft.use_state(0)

    # --- REFERENCIA PERSISTENTE ORIENTADA A DATOS NATIVOS ---
    valores_ingreso_ref = ft.use_ref(None)
    if valores_ingreso_ref.current is None:
        objetivo = list((problema_inicial or {}).get("objetivo", []) or [])
        restricciones = list((problema_inicial or {}).get("restricciones", []) or [])
        tipos_var = list((problema_inicial or {}).get("tipos_var", []) or [])

        if not tipos_var:
            enteras_old = list((problema_inicial or {}).get("enteras", []) or [])
            tipos_var = [
                "Entera" if (i < len(enteras_old) and enteras_old[i]) else "Continua"
                for i in range(max(len(objetivo), 2))
            ]

        num_variables = max(len(objetivo), 2)
        num_restricciones = max(len(restricciones), 1)

        # Rellenar con valores iniciales
        objetivo_vals = [str(val) for val in objetivo] + [""] * (num_variables - len(objetivo))
        tipos_var_vals = tipos_var + ["Entera"] * (num_variables - len(tipos_var))
        
        restricciones_vals = []
        for i in range(num_restricciones):
            r = restricciones[i] if i < len(restricciones) else {}
            coefs = list(r.get("coeficientes", []) or [])
            coefs_vals = [str(val) for val in coefs] + [""] * (num_variables - len(coefs))
            restricciones_vals.append({
                "coeficientes": coefs_vals,
                "signo": r.get("signo", "<="),
                "rhs": str(r.get("rhs", ""))
            })

        valores_ingreso_ref.current = {
            "tipo": (problema_inicial or {}).get("tipo", "MAX"),
            "objetivo": objetivo_vals,
            "restricciones": restricciones_vals,
            "tipos_var": tipos_var_vals
        }

    # Handlers para actualizar los datos nativos en tiempo real
    def cambiar_tipo(e: ft.ControlEvent) -> None:
        valores_ingreso_ref.current["tipo"] = e.control.value

    def cambiar_objetivo(idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["objetivo"][idx] = e.control.value
        return handler

    def cambiar_coef_restriccion(fila_idx: int, coef_idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["restricciones"][fila_idx]["coeficientes"][coef_idx] = e.control.value
        return handler

    def cambiar_signo_restriccion(fila_idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["restricciones"][fila_idx]["signo"] = e.control.value
        return handler

    def cambiar_rhs_restriccion(fila_idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["restricciones"][fila_idx]["rhs"] = e.control.value
        return handler

    def cambiar_tipo_var(idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["tipos_var"][idx] = e.control.value
        return handler

    def parse_numeric(value):
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

    # --- Acciones ---
    def agregar_variable(_e) -> None:
        valores_ingreso_ref.current["objetivo"].append("")
        for fila in valores_ingreso_ref.current["restricciones"]:
            fila["coeficientes"].append("")
        valores_ingreso_ref.current["tipos_var"].append("Entera")
        set_refresh_trigger(lambda x: x + 1)

    def eliminar_variable(_e) -> None:
        if len(valores_ingreso_ref.current["objetivo"]) > 1:
            valores_ingreso_ref.current["objetivo"].pop()
            for fila in valores_ingreso_ref.current["restricciones"]:
                if fila["coeficientes"]:
                    fila["coeficientes"].pop()
            valores_ingreso_ref.current["tipos_var"].pop()
            set_refresh_trigger(lambda x: x + 1)
        else:
            set_status_text_val(("No puedes eliminar la última variable.", RED))

    def agregar_restriccion(_e) -> None:
        num_vars = len(valores_ingreso_ref.current["objetivo"])
        valores_ingreso_ref.current["restricciones"].append({
            "coeficientes": [""] * num_vars,
            "signo": "<=",
            "rhs": ""
        })
        set_refresh_trigger(lambda x: x + 1)

    def eliminar_restriccion(_e) -> None:
        if len(valores_ingreso_ref.current["restricciones"]) > 1:
            valores_ingreso_ref.current["restricciones"].pop()
            set_refresh_trigger(lambda x: x + 1)
        else:
            set_status_text_val(("No puedes eliminar la última restricción.", RED))

    def restaurar_valores(_e) -> None:
        for i in range(len(valores_ingreso_ref.current["objetivo"])):
            valores_ingreso_ref.current["objetivo"][i] = ""
        for fila in valores_ingreso_ref.current["restricciones"]:
            for i in range(len(fila["coeficientes"])):
                fila["coeficientes"][i] = ""
            fila["rhs"] = ""
        set_status_text_val(("Valores vaciados.", AMBER))
        set_refresh_trigger(lambda x: x + 1)

    def restaurar_problema(_e) -> None:
        valores_ingreso_ref.current = {
            "tipo": "MAX",
            "objetivo": ["", ""],
            "restricciones": [
                {
                    "coeficientes": ["", ""],
                    "signo": "<=",
                    "rhs": ""
                }
            ],
            "tipos_var": ["Entera", "Entera"]
        }
        set_status_text_val(("Estructura restaurada.", AMBER))
        set_refresh_trigger(lambda x: x + 1)

    def restablecer_problema(_e) -> None:
        valores_ingreso_ref.current = {
            "tipo": "MAX",
            "objetivo": ["", ""],
            "restricciones": [
                {
                    "coeficientes": ["", ""],
                    "signo": "<=",
                    "rhs": ""
                }
            ],
            "tipos_var": ["Entera", "Entera"]
        }
        set_status_text_val(("Estructura reseteada.", AMBER))
        set_refresh_trigger(lambda x: x + 1)

    def armar_diccionario_entrada() -> dict:
        tipos = list(valores_ingreso_ref.current["tipos_var"])
        return {
            "tipo": valores_ingreso_ref.current["tipo"],
            "objetivo": [parse_numeric(val) for val in valores_ingreso_ref.current["objetivo"]],
            "restricciones": [
                {
                    "coeficientes": [parse_numeric(val) for val in fila["coeficientes"]],
                    "signo": fila["signo"],
                    "rhs": parse_numeric(fila["rhs"]),
                }
                for fila in valores_ingreso_ref.current["restricciones"]
            ],
            "tipos_var": tipos,
            "enteras": [t in ("Entera", "Binaria") for t in tipos],
        }

    def guardar_problema(_e) -> None:
        datos = armar_diccionario_entrada()
        controlador.problema_activo = deepcopy(datos)
        try:
            if hasattr(controlador, "operar_problema"):
                resultado = controlador.operar_problema(datos, 1)
                if resultado is not None:
                    set_status_text_val(("✓ Problema guardado y establecido como activo.", GREEN))
                else:
                    set_status_text_val(("✗ No fue posible guardar el problema.", RED))
            else:
                set_status_text_val(("✓ Problema guardado localmente (Solvers inactivos).", GREEN))
        except Exception as err:
            set_status_text_val((f"✗ Error al guardar: {err}", RED))

    # --- Renderizado Layout ---
    def build_mode_toggle() -> ft.Container:
        def modo_btn(texto: str, activo: bool, on_click) -> ft.ElevatedButton:
            return ft.ElevatedButton(
                content=ft.Text(texto, size=11, color="white"),
                bgcolor=ACCENT_COLOR if activo else "#374151",
                on_click=on_click,
            )

        return ft.Container(
            content=ft.Row([
                ft.Text("Modo:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                modo_btn(
                    "Programación Lineal", activo=False,
                    on_click=lambda _e: cambiar_modo("LP") if cambiar_modo else None,
                ),
                modo_btn(
                    "Programación Lineal Entera", activo=True,
                    on_click=lambda _e: None,
                ),
            ], spacing=8),
            padding=10, border_radius=8, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, "#374151"), bottom=ft.BorderSide(1, "#374151"),
                left=ft.BorderSide(1, "#374151"), right=ft.BorderSide(1, "#374151"),
            ),
        )

    def build_integer_section() -> ft.Container:
        dropdowns = []
        for idx, t_var in enumerate(valores_ingreso_ref.current["tipos_var"]):
            dd = _nuevo_tipo_dropdown(idx, t_var, on_select=cambiar_tipo_var(idx))
            dropdowns.append(dd)

        rows: list[ft.Row] = []
        max_per_row = 9
        for i in range(0, len(dropdowns), max_per_row):
            rows.append(
                ft.Row(
                    dropdowns[i:i + max_per_row],
                    wrap=False, spacing=10, alignment=ft.MainAxisAlignment.START, expand=False,
                )
            )

        label_width = 120
        spacing = 10
        total_width = len(dropdowns) * label_width + max(0, len(dropdowns) - 1) * spacing
        container_width = min(total_width + 32, 1220) if total_width > 0 else None

        return ft.Container(
            width=container_width,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.FUNCTIONS, size=14, color=ACCENT_COLOR),
                    ft.Text("Tipo de variable", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ], spacing=6),
                ft.Text("Continua: real · Entera: ℤ · Binaria: solo 0 o 1", size=11, color=TEXT_MUTED),
                *rows,
            ], spacing=10),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, "#374151"), bottom=ft.BorderSide(1, "#374151"),
                left=ft.BorderSide(1, "#374151"), right=ft.BorderSide(1, "#374151"),
            ),
        )

    def build_restriction_row(indice: int, fila: dict) -> ft.Container:
        campos = []
        for i, val in enumerate(fila["coeficientes"]):
            campo_coef = _campo(f"X{i+1}", val)
            campo_coef.on_change = cambiar_coef_restriccion(indice - 1, i)
            campos.append(campo_coef)
            if i < len(fila["coeficientes"]) - 1:
                campos.append(ft.Text("+", color=TEXT_MUTED, size=12))

        signo_dropdown = ft.Dropdown(
            value=fila["signo"],
            options=[ft.dropdown.Option("<="), ft.dropdown.Option(">="), ft.dropdown.Option("==")],
            width=90,
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            border_radius=8,
            on_select=cambiar_signo_restriccion(indice - 1),
        )

        rhs_field = _campo("RHS", fila["rhs"])
        rhs_field.on_change = cambiar_rhs_restriccion(indice - 1)

        return ft.Container(
            content=ft.Column([
                ft.Text(f"Restricción {indice}", size=12, weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
                ft.Row(campos + [signo_dropdown, rhs_field], wrap=True, spacing=6),
            ], spacing=8),
            padding=12, border_radius=10, bgcolor="#12141f",
            border=ft.Border(
                top=ft.BorderSide(1, "#252836"), bottom=ft.BorderSide(1, "#252836"),
                left=ft.BorderSide(1, "#252836"), right=ft.BorderSide(1, "#252836"),
            ),
        )

    fo_controls = [ft.Text("Z =", color=TEXT_MUTED, size=13)]
    for i, val in enumerate(valores_ingreso_ref.current["objetivo"]):
        campo = _campo(f"X{i+1}", val)
        campo.on_change = cambiar_objetivo(i)
        fo_controls.append(campo)
        if i < len(valores_ingreso_ref.current["objetivo"]) - 1:
            fo_controls.append(ft.Text("+", color=TEXT_MUTED, size=14))

    tipo_dropdown = ft.Dropdown(
        label="Optimización",
        value=valores_ingreso_ref.current["tipo"],
        options=[ft.dropdown.Option("MAX"), ft.dropdown.Option("MIN")],
        width=160,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        border_radius=8,
        on_select=cambiar_tipo,
    )

    fo_section = _seccion(
        "Función objetivo",
        ft.Column([
            tipo_dropdown,
            ft.Row(fo_controls, wrap=True, spacing=6),
            ft.Row([
                _btn("Añadir variable", ft.Icons.ADD, agregar_variable),
                _btn("Eliminar variable", ft.Icons.REMOVE, eliminar_variable, color="#374151"),
            ], spacing=8, wrap=True),
        ], spacing=10),
    )

    restricciones_col = ft.Column(spacing=10)
    for i, fila in enumerate(valores_ingreso_ref.current["restricciones"], start=1):
        restricciones_col.controls.append(build_restriction_row(i, fila))
    restricciones_col.controls.append(
        ft.Row([
            _btn("Añadir restricción", ft.Icons.ADD_CIRCLE_OUTLINE, agregar_restriccion),
            _btn("Eliminar restricción", ft.Icons.REMOVE_CIRCLE_OUTLINE, eliminar_restriccion, color="#374151"),
        ], spacing=8, wrap=True),
    )
    rest_section = _seccion("Restricciones", restricciones_col)

    status_text_widget = ft.Text(
        status_text_val[0],
        size=12,
        color=status_text_val[1],
        visible=bool(status_text_val[0])
    )

    return ft.Container(
        content=ft.Column([
            build_mode_toggle(),
            ft.Column([
                ft.Text("Ingresar Problema (Entero)", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Define función objetivo, tipo de variables y restricciones.", size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            fo_section,
            build_integer_section(),
            rest_section,
            ft.Row([
                _btn("Guardar problema", ft.Icons.SAVE, guardar_problema, color=GREEN),
                _btn("Restaurar valores", ft.Icons.REFRESH, restaurar_valores, color="#374151"),
                _btn("Restaurar problema", ft.Icons.UNDO, restaurar_problema, color="#374151"),
                _btn("Restablecer", ft.Icons.RESTART_ALT, restablecer_problema, color="#374151"),
            ], spacing=8, wrap=True),
            status_text_widget,
        ], spacing=16, scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=ft.CrossAxisAlignment.START),
        expand=True,
    )