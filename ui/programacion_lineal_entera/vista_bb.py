# ui/vista_bb.py
"""
vista_bb.py
===========
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Responsable del renderizado del árbol Branch & Bound para programación entera.
"""

from __future__ import annotations
from fractions import Fraction
from typing import Any, Optional
import flet as ft
from src.controller.controlador_entera import ControladorEntera

ACCENT_COLOR = "#7c3aed"
BG_CARD      = "#161822"
BG_TABLE     = "#0d0f1a"
BORDER_COLOR = "#2a2d3a"
TEXT_MUTED   = "#6b7280"
TEXT_PRIMARY = "#f0f0f0"
GREEN        = "#7dd3a8"
AMBER        = "#f6ad55"
RED          = "#ef645f"
BLUE         = "#63b3ed"


def _formatear_fo(tipo: str, objetivo: list) -> str:
    if not objetivo:
        return f"{tipo} Z = 0"
    terminos = []
    for i, coef in enumerate(objetivo):
        try:
            c = float(coef)
        except Exception:
            c = 0.0
        if c == 0:
            continue
        var = f"X{i+1}"
        if c > 0:
            terminos.append(
                f"{'+ ' if terminos else ''}{c:.4g}{var}"
                if abs(c) != 1 else f"{'+ ' if terminos else ''}{var}"
            )
        else:
            terminos.append(
                f"- {abs(c):.4g}{var}" if abs(c) != 1 else f"- {var}"
            )
    return f"{tipo} Z = {' '.join(terminos) or '0'}"


# Colores y etiquetas para cada estado de nodo
_ESTADO_CFG = {
    "optimo":              (GREEN,        "✓ Óptimo entero"),
    "podado_cota":         (RED,          "Podado · cota"),
    "podado_infactible":   (RED,          "Podado · infactible"),
    "podado":              (RED,          "Podado"),
    "ramificado":          (ACCENT_COLOR, "Ramificado"),
    "activo":              (BLUE,         "Activo"),
}


def _fmt(valor: Any) -> str:
    if hasattr(valor, "item"):
        valor = valor.item()
    if isinstance(valor, Fraction):
        return str(valor)
    if isinstance(valor, float):
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")
        return texto if texto else "0"
    return str(valor)


def _crear_alerta_status(mensaje: str, color: str, icono=None) -> ft.Row:
    if icono is None:
        icono = ft.Icons.CHECK_CIRCLE if color == GREEN else ft.Icons.WARNING_AMBER
    return ft.Row([
        ft.Container(
            content=ft.Row(
                [ft.Icon(icono, color=color, size=15),
                 ft.Text(mensaje, color=color, size=12)],
                spacing=8,
            ),
            padding=14, border_radius=8, bgcolor=color + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"),
                left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44"),
            ),
        )
    ])


def _badge_estado(estado: str) -> ft.Container:
    color, label = _ESTADO_CFG.get(estado, (TEXT_MUTED, estado))
    return ft.Container(
        content=ft.Text(label, size=10, color=color, weight=ft.FontWeight.W_600),
        padding=8, bgcolor=color + "22", border_radius=99,
    )


def _crear_nodo_card(nodo: dict) -> ft.Control:
    nodo_id   = nodo.get("id", 0)
    nivel     = nodo.get("nivel", 0)
    estado    = nodo.get("estado", "activo")
    z_relajada = nodo.get("z_relajada")
    variables = nodo.get("variables") or []
    condicion = nodo.get("condicion", "")
    padre_id  = nodo.get("padre_id")
    mensaje   = nodo.get("mensaje", "")

    color_estado, _ = _ESTADO_CFG.get(estado, (BORDER_COLOR, ""))
    es_podado = estado in ("podado", "podado_cota", "podado_infactible")
    z_str = _fmt(z_relajada) if z_relajada is not None else "N/D"

    encabezado_items: list[ft.Control] = [
        ft.Text(f"Nodo {nodo_id}", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
    ]
    if padre_id is not None:
        encabezado_items.append(
            ft.Text(f"· hijo de N{padre_id}", size=11, color=TEXT_MUTED)
        )
    if condicion:
        encabezado_items.append(
            ft.Container(
                content=ft.Text(condicion, size=10, color=BLUE, weight=ft.FontWeight.W_500),
                padding=6, bgcolor=BLUE + "22", border_radius=4,
            )
        )
    encabezado_items.append(_badge_estado(estado))

    valores_items: list[ft.Control] = [
        ft.Container(
            content=ft.Column([
                ft.Text("Z relajada", size=10, color=TEXT_MUTED),
                ft.Text(
                    z_str, size=16,
                    color=GREEN if estado == "optimo" else BLUE,
                    weight=ft.FontWeight.BOLD,
                ),
            ], spacing=2),
            padding=10, border_radius=6, bgcolor="#1e2130",
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
            ),
        )
    ]
    for i, v in enumerate(variables):
        valores_items.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(f"X{i+1}", size=10, color=TEXT_MUTED),
                    ft.Text(_fmt(v), size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_500),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=10, border_radius=6, bgcolor="#1e2130",
                border=ft.Border(
                    top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                    left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
                ),
            )
        )

    contenido = ft.Column([
        ft.Row(encabezado_items, spacing=6, wrap=True),
        ft.Row(valores_items, spacing=6, wrap=True),
        *([ft.Text(mensaje, size=11, color=TEXT_MUTED, italic=True)] if mensaje else []),
    ], spacing=8)

    return ft.Row([
        ft.Container(width=nivel * 22),        # sangría según nivel
        ft.Container(
            content=contenido,
            padding=12, border_radius=10, bgcolor=BG_CARD,
            opacity=0.5 if es_podado else 1.0,
            border=ft.Border(
                top=ft.BorderSide(1, color_estado + ("55" if es_podado else "")),
                bottom=ft.BorderSide(1, color_estado + ("55" if es_podado else "")),
                left=ft.BorderSide(3, color_estado + ("55" if es_podado else "")),
                right=ft.BorderSide(1, BORDER_COLOR),
            ),
            expand=True,
        ),
    ], spacing=0)


def _tarjeta_resumen(resultado: dict, problema: dict) -> ft.Container:
    tipo = problema.get("tipo", "MAX")
    objetivo = problema.get("objetivo", [])
    fo_str = _formatear_fo(tipo, objetivo)

    z_optimo  = resultado.get("z_optimo")
    variables = resultado.get("variables_decision") or []
    estado    = resultado.get("estado", "")
    mensaje   = resultado.get("mensaje", "")
    n_expl    = resultado.get("nodos_explorados", 0)
    n_pod     = resultado.get("nodos_podados", 0)

    z_str    = _fmt(z_optimo) if z_optimo is not None else "N/D"
    vars_str = ", ".join(f"X{i+1}={_fmt(v)}" for i, v in enumerate(variables)) or "N/D"

    def _stat(titulo: str, valor: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=10, color=TEXT_MUTED),
                ft.Text(valor, size=17, color=color, weight=ft.FontWeight.BOLD),
            ], spacing=2),
            padding=14, border_radius=8, bgcolor="#1e2130",
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
            ),
        )

    cuerpo: list[ft.Control] = [
        ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
        ft.Row([
            _stat("Z óptimo entero", z_str, GREEN),
            _stat("Variables", vars_str, TEXT_PRIMARY),
            _stat("Nodos explorados", str(n_expl), BLUE),
            _stat("Nodos podados", str(n_pod), RED),
        ], spacing=8, wrap=True),
    ]
    if estado:
        cuerpo.append(ft.Text(f"Estado: {estado}", size=11, color=TEXT_MUTED, italic=True))
    if mensaje:
        cuerpo.append(ft.Text(mensaje, size=11, color=TEXT_MUTED, italic=True))

    return ft.Container(
        content=ft.Column(cuerpo, spacing=10),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"),
            left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66"),
        ),
    )


def _leyenda() -> ft.Row:
    items = [
        (ACCENT_COLOR, "Ramificado"),
        (BLUE,         "Activo"),
        (GREEN,        "Óptimo entero"),
        (RED,          "Podado"),
    ]
    controles: list[ft.Control] = [
        ft.Text("Leyenda:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500)
    ]
    for color, label in items:
        controles.append(
            ft.Row([
                ft.Container(width=10, height=10, border_radius=2, bgcolor=color),
                ft.Text(label, size=10, color=TEXT_MUTED),
            ], spacing=4)
        )
    return ft.Row(controles, spacing=14, wrap=True)


def _renderizar_arbol(resultado: dict, problema: dict) -> list[ft.Control]:
    controles: list[ft.Control] = [
        _tarjeta_resumen(resultado, problema),
        _leyenda(),
        ft.Text("Árbol de ramificación", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
    ]

    nodos = resultado.get("nodos") or []
    if not nodos:
        controles.append(
            ft.Container(
                content=ft.Text(
                    "El controlador no devolvió nodos. Verifica que resolver_entera retorne la clave 'nodos'.",
                    color=AMBER, size=12, italic=True,
                ),
                padding=16, border_radius=10, bgcolor=BG_CARD,
                border=ft.Border(
                    top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"),
                    left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44"),
                ),
            )
        )
        return controles

    for nodo in nodos:
        controles.append(_crear_nodo_card(nodo))

    return controles


@ft.component
def VistaBB(controlador: ControladorEntera):
    problema = getattr(controlador, "problema_activo", None)

    header = ft.Column([
        ft.Text("Branch & Bound", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Árbol de ramificación y poda para programación entera.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Sin problema activo
    if not problema:
        status_row = _crear_alerta_status("Ingresa o selecciona un problema primero.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.DEVICE_HUB, color=TEXT_MUTED, size=48),
                ft.Text("Sin problema activo", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=48, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 2. Sin variables enteras definidas
    enteras = problema.get("enteras") or []
    if not any(enteras):
        status_row = _crear_alerta_status("No hay variables enteras definidas. Márcalas en la vista de ingreso.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER, color=AMBER, size=40),
                ft.Text("Ninguna variable marcada como entera.\nVe a Ingresar y activa los checks de integridad.", color=AMBER, text_align=ft.TextAlign.CENTER, size=13),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"),
                left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44"),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 3. Controlador sin método resolver_entera
    if not hasattr(controlador, "resolver_entera"):
        status_row = _crear_alerta_status("El controlador aún no implementa resolver_entera(problema).", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.BUILD, color=AMBER, size=40),
                ft.Text("Implementa controlador.resolver_entera(problema)\npara ver el árbol Branch & Bound.", color=AMBER, text_align=ft.TextAlign.CENTER, size=13),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"),
                left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44"),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 4. Resolver
    resultado = controlador.resolver_entera(problema)

    # 5. Sin resultado
    if resultado is None:
        status_row = _crear_alerta_status("El controlador devolvió respuesta vacía.", RED)
        placeholder = ft.Container(
            content=ft.Text("No se pudo resolver el problema entero.", color=RED),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"),
                left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44"),
            ),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 6. Con resultado
    estado = resultado.get("estado", "")
    if estado == "optimo":
        status_row = _crear_alerta_status("Solución entera óptima encontrada.", GREEN)
    elif estado == "infactible":
        status_row = _crear_alerta_status("El problema no tiene solución entera factible.", RED, ft.Icons.ERROR_OUTLINE)
    elif estado == "no_acotado":
        status_row = _crear_alerta_status("El problema no está acotado.", RED, ft.Icons.ERROR_OUTLINE)
    else:
        status_row = _crear_alerta_status(f"Atención: estado → {estado}", AMBER)

    arbol_controls = ft.Column(_renderizar_arbol(resultado, problema), spacing=12)

    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, arbol_controls],
        expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
    )
