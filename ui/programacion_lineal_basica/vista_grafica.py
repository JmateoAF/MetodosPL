# ui/vista_grafica.py
"""
vista_grafica.py
================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Se encarga de representar de forma bidimensional (2D) la región factible y el 
punto óptimo del modelo lineal, acompañado de su análisis analítico completo.
"""

from __future__ import annotations
from typing import List, Optional
import flet as ft

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal.respuesta import RespuestaSciPyPL
from src.utils.programacion_lineal_basica.graficador import generar_grafico_cartesiano
from src.controller.controlador_lineal import ControladorLineal

# Paleta de colores institucional
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BORDER_COLOR: str = "#2a2d3a"
TEXT_MUTED: str = "#6b7280"
TEXT_PRIMARY: str = "#f0f0f0"
GREEN: str = "#7dd3a8"
AMBER: str = "#f6ad55"
RED: str = "#ef645f"
BLUE: str = "#63b3ed"


def _formatear_funcion_objetivo_ui(tipo: TipoOptimizacion, objetivo: List[float | int]) -> str:
    if not objetivo:
        return f"{tipo.value} Z = 0"
    terminos: List[str] = []
    for i, coef in enumerate(objetivo):
        val_float = float(coef)
        if val_float == 0.0:
            continue
        variable = f"X{i+1}"
        if val_float > 0.0:
            prefijo = "+ " if terminos else ""
            coef_str = f"{val_float:.4g}" if val_float != 1.0 else ""
            terminos.append(f"{prefijo}{coef_str}{variable}")
        else:
            coef_str = f"{abs(val_float):.4g}" if abs(val_float) != 1.0 else ""
            terminos.append(f"- {coef_str}{variable}")
    return f"{tipo.value} Z = {' '.join(terminos) or '0'}"


def _formatear_valor_numerico(valor: Optional[float]) -> str:
    if valor is None:
        return "N/D"
    val_float = float(valor)
    if val_float.is_integer():
        return str(int(val_float))
    texto_formateado = f"{val_float:.6f}".rstrip("0").rstrip(".")
    return texto_formateado if texto_formateado else "0"


def _crear_tarjeta_metrica_ui(titulo: str, valor: str, color_hex: str) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(titulo, size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Text(valor, size=18, color=color_hex, weight=ft.FontWeight.BOLD),
            ],
            spacing=4
        ),
        padding=16,
        border_radius=10,
        bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
            left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
        ),
        expand=True,
    )


def _crear_alerta_status(mensaje: str, color_hex: str, icono: ft.Icons = ft.Icons.WARNING_AMBER) -> ft.Row:
    return ft.Row([
        ft.Container(
            content=ft.Row([ft.Icon(icono, color=color_hex, size=15), ft.Text(mensaje, color=color_hex, size=12)], spacing=8),
            padding=14,
            border_radius=8,
            bgcolor=color_hex + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color_hex + "44"), bottom=ft.BorderSide(1, color_hex + "44"),
                left=ft.BorderSide(1, color_hex + "44"), right=ft.BorderSide(1, color_hex + "44")
            ),
        )
    ])


@ft.component
def VistaGrafica(controlador: ControladorLineal):
    problema: Optional[ProblemaPL] = controlador.problema_activo

    header = ft.Column([
        ft.Text("Análisis Geométrico (Método Gráfico)", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Visualización de la región factible e isocuanta óptima. Exclusivo para modelos de 2 variables.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Caso sin problema activo
    if problema is None:
        status_row = _crear_alerta_status("Ingresa o selecciona un problema matemático primero.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Column([
            ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_MUTED, size=48),
            ft.Text("Sin información geométrica para renderizar.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        img_container = ft.Container(
            content=placeholder,
            alignment=ft.alignment.Alignment(0, 0),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            expand=True,
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, img_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 2. Restricción dimensional (R^2)
    if problema.total_variables != 2:
        status_row = _crear_alerta_status(f"Incompatible: El método requiere 2 variables ({problema.total_variables} detectadas).", RED, ft.Icons.ERROR_OUTLINE)
        error_content = ft.Column([
            ft.Icon(ft.Icons.ERROR_OUTLINE, color=RED, size=40),
            ft.Text(f"El modelo ingresado pertenece a un plano de {problema.total_variables} dimensiones.\nEl renderizado geométrico es exclusivo para R² (2 variables).",
                    color=RED, text_align=ft.TextAlign.CENTER, size=13),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        img_container = ft.Container(
            content=error_content,
            alignment=ft.alignment.Alignment(0, 0),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            expand=True,
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, img_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 3. Resolver
    resultado: Optional[RespuestaSciPyPL] = controlador.resolver_LP(problema, 1)

    if resultado is None:
        status_row = _crear_alerta_status("Error crítico al invocar el motor de cálculo.", RED, ft.Icons.ERROR)
        placeholder = ft.Column([
            ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_MUTED, size=48),
            ft.Text("Sin información geométrica para renderizar.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        img_container = ft.Container(
            content=placeholder,
            alignment=ft.alignment.Alignment(0, 0),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            expand=True,
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, img_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 4. Gestión del estado de salida
    if resultado.estado == EstadoProblema.OPTIMO:
        status_row = _crear_alerta_status("Análisis geométrico y óptimo generado correctamente.", GREEN, ft.Icons.CHECK_CIRCLE)
    else:
        status_row = _crear_alerta_status(f"Atención Geométrica: {resultado.mensaje}", AMBER, ft.Icons.WARNING_AMBER)

    # Trazado de gráfico
    try:
        img_b64 = generar_grafico_cartesiano(problema, resultado)
        if img_b64:
            img_control = ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN)
        else:
            img_control = ft.Text("No fue posible trazar la geometría del sistema.", color=RED)
    except Exception as e:
        img_control = ft.Container(
            content=ft.Text(f"Error de renderizado gráfico: {str(e)[:100]}", color=RED, size=11),
            padding=14, border_radius=12, 
            border=ft.Border(top=ft.BorderSide(1, RED), bottom=ft.BorderSide(1, RED), left=ft.BorderSide(1, RED), right=ft.BorderSide(1, RED)),
        )

    img_container = ft.Container(
        content=img_control,
        alignment=ft.alignment.Alignment(0, 0),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
            left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
        ),
        expand=True,
    )

    fo_formateada = _formatear_funcion_objetivo_ui(problema.tipo, problema.objetivo)
    z_optimo_str = _formatear_valor_numerico(resultado.fun)
    vector_solucion: List[float] = resultado.x if resultado.x is not None else []
    vector_holguras: List[float] = resultado.slack if resultado.slack is not None else []

    tarjetas_metricas = ft.Row(
        [
            _crear_tarjeta_metrica_ui("Valor Óptimo Z", z_optimo_str, GREEN),
            _crear_tarjeta_metrica_ui("Iteraciones Analíticas", str(resultado.nit), BLUE),
        ],
        spacing=10
    )

    bloque_variables = ft.Container(
        content=ft.Column(
            [
                ft.Text("Coordenadas del Vértice (X1, X2)", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(f"X{i+1}", size=11, color=TEXT_MUTED),
                                    ft.Text(_formatear_valor_numerico(v), size=16, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=16, border_radius=8, bgcolor="#1e2130",
                            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        )
                        for i, v in enumerate(vector_solucion)
                    ],
                    wrap=True, spacing=8
                ),
            ],
            spacing=10
        ),
        padding=16, border_radius=12, bgcolor=BG_CARD, expand=True,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )

    bloque_holguras = ft.Container(
        content=ft.Column(
            [
                ft.Text("Holguras del Sistema", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(f"S{j+1}", size=11, color=TEXT_MUTED),
                                    ft.Text(_formatear_valor_numerico(h), size=14, color=AMBER if float(h) > 0 else TEXT_MUTED, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=12, border_radius=8, bgcolor="#1a1c29",
                            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        )
                        for j, h in enumerate(vector_holguras)
                    ],
                    wrap=True, spacing=8
                ) if vector_holguras else ft.Text("N/A", size=11, color=TEXT_MUTED, italic=True),
            ],
            spacing=10
        ),
        padding=16, border_radius=12, bgcolor=BG_CARD, expand=True,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )

    fila_vectores = ft.Row([bloque_variables, bloque_holguras], spacing=10, alignment=ft.MainAxisAlignment.START)

    tarjeta_fo = ft.Container(
        content=ft.Column(
            [
                ft.Text(fo_formateada, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                ft.Text(f"Estado del Motor: {resultado.mensaje}", size=11, color=TEXT_MUTED, italic=True)
            ],
            spacing=6
        ),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
    )

    resultado_container = ft.Column([tarjeta_fo, tarjetas_metricas, fila_vectores], spacing=10)

    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, resultado_container, img_container],
        expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
    )
