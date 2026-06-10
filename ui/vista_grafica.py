# ui/vista_grafica.py
"""
vista_grafica.py
================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Se encarga de representar de forma bidimensional (2D) la región factible y el 
punto óptimo del modelo lineal, acompañado de su análisis analítico completo.

Responsabilidades:
    - Validar estáticamente que el modelo posea exactamente dos variables de decisión.
    - Ejecutar la resolución analítica a través del Controlador.
    - Consumir el módulo 'graficador' para obtener el renderizado en Base64.
    - Exponer la métrica completa de SciPy (incluyendo holguras e iteraciones).

Autor: UI Graphic View Module — MVC Linear Optimizer
"""

from __future__ import annotations
from typing import List, Optional
import flet as ft

# Importaciones estrictas de la capa de Dominio y Utilidades del Sistema
from src.models.entity.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.problema import ProblemaPL
from src.models.entity.respuesta import RespuestaSciPyPL
from src.utils.graficador import generar_grafico_cartesiano

# Paleta de colores institucional para mantener la consistencia estética
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
    """Transforma el vector de coeficientes inmutables en una ecuación algebraica legible."""
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
    """Formatea valores de punto flotante de SciPy eliminando ceros a la derecha redundantes."""
    if valor is None:
        return "N/D"
    val_float = float(valor)
    if val_float.is_integer():
        return str(int(val_float))
    texto_formateado = f"{val_float:.6f}".rstrip("0").rstrip(".")
    return texto_formateado if texto_formateado else "0"


def _crear_tarjeta_metrica_ui(titulo: str, valor: str, color_hex: str) -> ft.Container:
    """Factory function para generar tarjetas de métricas globales (KPIs) homogéneas."""
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


class VistaGrafica(ft.Column):
    """
    Vista modular encargada de la ejecución y representación del Método Gráfico,
    restringida matemáticamente a modelos de R^2.
    """

    def __init__(self, controlador) -> None:
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador

        # Contenedores dinámicos del Layout reactivo
        self.status_row: ft.Row = ft.Row([], visible=False)
        self.resultado_container: ft.Column = ft.Column(spacing=10)
        
        # Lienzo dedicado exclusivamente al renderizado del gráfico de Matplotlib
        self.img_container: ft.Container = ft.Container(
            alignment=ft.alignment.Alignment(0, 0),
            padding=16,
            border_radius=12,
            bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
            ),
            expand=True,
        )

        # Configuración del esqueleto estático de la ventana
        self.controls = [
            ft.Column([
                ft.Text("Análisis Geométrico (Método Gráfico)", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Visualización de la región factible e isocuanta óptima. Exclusivo para modelos de 2 variables.", size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.resultado_container,
            self.img_container,
        ]
        self.refresh()

    def _mostrar_alerta_status(self, mensaje: str, color_hex: str, icono: Optional[ft.Icons] = None) -> None:
        """Pinta barras informativas de alerta contextual en el Layout superior."""
        if icono is None:
            icono = ft.Icons.CHECK_CIRCLE if color_hex == GREEN else ft.Icons.WARNING_AMBER
            
        self.status_row.visible = True
        self.status_row.controls = [
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
        ]

    def refresh(self) -> None:
        """Flujo funcional que evalúa el problema, ejecuta la gráfica y dibuja los KPI."""
        problema: Optional[ProblemaPL] = self.controlador.problema_activo

        # Validación 1: Existencia de problema activo
        if problema is None:
            self._mostrar_alerta_status("Ingresa o selecciona un problema matemático primero.", AMBER, ft.Icons.INFO_OUTLINE)
            self._renderizar_placeholder_vacio()
            self._safe_update_ui()
            return

        # Validación 2: Restricción dimensional (R^2)
        if problema.total_variables != 2:
            self._mostrar_alerta_status(f"Incompatible: El método requiere 2 variables ({problema.total_variables} detectadas).", RED, ft.Icons.ERROR_OUTLINE)
            self.img_container.content = ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=RED, size=40),
                ft.Text(f"El modelo ingresado pertenece a un plano de {problema.total_variables} dimensiones.\nEl renderizado geométrico es exclusivo para R² (2 variables).",
                        color=RED, text_align=ft.TextAlign.CENTER, size=13),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.resultado_container.controls = []
            self._safe_update_ui()
            return

        # Ejecución analítica a través del Controlador
        resultado: Optional[RespuestaSciPyPL] = self.controlador.resolver_LP(problema, 1)

        if resultado is None:
            self._mostrar_alerta_status("Error crítico al invocar el motor de cálculo.", RED, ft.Icons.ERROR)
            self._renderizar_placeholder_vacio()
            self._safe_update_ui()
            return

        # Gestión del estado de salida
        if resultado.estado == EstadoProblema.OPTIMO:
            self._mostrar_alerta_status("Análisis geométrico y óptimo generado correctamente.", GREEN)
        else:
            self._mostrar_alerta_status(f"Atención Geométrica: {resultado.mensaje}", AMBER)

        # Generar gráfico y renderizar metadata
        self._gestionar_dibujo_grafico(problema, resultado)
        self._renderizar_metadata_analitica(problema, resultado)
        self._safe_update_ui()

    def _renderizar_placeholder_vacio(self) -> None:
        """Dibuja un lienzo vacío en caso de ausencia de problema o error."""
        self.img_container.content = ft.Column([
            ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_MUTED, size=48),
            ft.Text("Sin información geométrica para renderizar.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.resultado_container.controls = []

    def _gestionar_dibujo_grafico(self, problema: ProblemaPL, resultado: RespuestaSciPyPL) -> None:
        """Inyecta los datos al utilitario asíncrono y decodifica la imagen generada."""
        try:
            img_b64 = generar_grafico_cartesiano(problema, resultado)
            if img_b64:
                self.img_container.content = ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN)
            else:
                self.img_container.content = ft.Text("No fue posible trazar la geometría del sistema.", color=RED)
        except Exception as e:
            self.img_container.content = ft.Container(
                content=ft.Text(f"Error de renderizado gráfico: {str(e)[:100]}", color=RED, size=11),
                padding=14, border_radius=12, 
                border=ft.Border(top=ft.BorderSide(1, RED), bottom=ft.BorderSide(1, RED), left=ft.BorderSide(1, RED), right=ft.BorderSide(1, RED)),
            )

    def _renderizar_metadata_analitica(self, problema: ProblemaPL, resultado: RespuestaSciPyPL) -> None:
        """Construye las tarjetas de resultados, incluyendo Z, variables, holguras e iteraciones."""
        fo_formateada = _formatear_funcion_objetivo_ui(problema.tipo, problema.objetivo)
        z_optimo_str = _formatear_valor_numerico(resultado.fun)
        vector_solucion: List[float] = resultado.x if resultado.x is not None else []
        vector_holguras: List[float] = resultado.slack if resultado.slack is not None else []

        # --- Tarjetas Superiores (KPIs) ---
        tarjetas_metricas = ft.Row(
            [
                _crear_tarjeta_metrica_ui("Valor Óptimo Z", z_optimo_str, GREEN),
                _crear_tarjeta_metrica_ui("Iteraciones Analíticas", str(resultado.nit), BLUE),
            ],
            spacing=10
        )

        # --- Tarjetas de Vectores (Variables de Decisión y Holguras) ---
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

        # --- Tarjeta Informativa de la Función Objetivo ---
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

        self.resultado_container.controls = [tarjeta_fo, tarjetas_metricas, fila_vectores]

    def _safe_update_ui(self) -> None:
        """Evita la caída del hilo en actualizaciones asíncronas de Flet."""
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def build(self) -> ft.Control:
        self.refresh()
        return self
