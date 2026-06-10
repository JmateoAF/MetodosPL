# vista_historial.py
"""
vista_historial.py
==================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Se encarga de renderizar de forma elegante y asíncrona el histórico de modelos.

Responsabilidades:
    - Consultar el historial fuertemente tipado del Controlador.
    - Formatear pedagógicamente ecuaciones y restricciones lineales en lenguaje natural.
    - Gestionar la activación de sesiones o clonación de objetos inmutables del dominio.

Autor: UI History View Module — MVC Linear Optimizer
"""

from __future__ import annotations
from typing import List
import flet as ft

# Importaciones estrictas de la capa de Dominio del Sistema
from src.models.entity.programacion_lineal.enums import TipoOptimizacion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion

# Paleta de colores institucional para mantener la consistencia estética
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BORDER_COLOR: str = "#2a2d3a"
TEXT_MUTED: str = "#6b7280"
TEXT_PRIMARY: str = "#f0f0f0"
GREEN: str = "#7dd3a8"
AMBER: str = "#f6ad55"
RED: str = "#ef645f"


def _formatear_funcion_objetivo_pedagogica(tipo: TipoOptimizacion, objetivo: List[float | int]) -> str:
    """Transforma el vector de coeficientes inmutables en una ecuación algebraica limpia."""
    if not objetivo:
        return f"{tipo.value} Z = 0"
    
    terminos: List[str] = []
    for i, coef in enumerate(objetivo):
        val_float = float(coef)
        if val_float == 0.0:
            continue
        
        variable = f"X{i+1}"
        # Manejo estético de signos y coeficientes unitarios implícitos (ej: +1X1 -> + X1)
        if val_float > 0.0:
            prefijo = "+ " if terminos else ""
            coef_str = f"{val_float:.4g}" if val_float != 1.0 else ""
            terminos.append(f"{prefijo}{coef_str}{variable}")
        else:
            coef_str = f"{abs(val_float):.4g}" if abs(val_float) != 1.0 else ""
            terminos.append(f"- {coef_str}{variable}")
            
    return f"{tipo.value} Z = {' '.join(terminos) or '0'}"


def _badge_ui(texto: str, color_hex: str) -> ft.Container:
    """Componente utilitario inmutable para pintar etiquetas de control visual."""
    return ft.Container(
        content=ft.Text(texto, size=10, color="white", weight=ft.FontWeight.W_600),
        padding=ft.padding.all(6),
        bgcolor=color_hex,
        border_radius=99,
    )


def _boton_accion_ui(texto: str, icono: ft.Icons, on_click, color: str = ACCENT_COLOR) -> ft.ElevatedButton:
    """Factory function para estandarizar los disparadores de eventos táctiles."""
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(icono, size=14, color="white"), 
                ft.Text(texto, size=11, color="white")
            ],
            spacing=5, 
            tight=True,
        ),
        bgcolor=color,
        on_click=on_click,
    )


class VistaHistorial(ft.Column):
    """
    Vista modular encargada de listar, activar y remover instancias inmutables 
    de problemas guardados en el dominio de la sesión.
    """

    def __init__(self, controlador, navegar_a=None) -> None:
        # Inicialización nativa de la estructura de columna de Flet v0.85 con Scroll automático
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.navegar_a = navegar_a

        # Contenedores dinámicos de renderizado
        self.cards_column: ft.Column = ft.Column(spacing=10, expand=True)
        self.status_row: ft.Row = ft.Row([], visible=False)

        # Inyección canónica del esqueleto estático de la ventana
        self.controls = [
            ft.Column([
                ft.Text("Historial de Problemas", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Consulta, carga, clona/edita o elimina problemas guardados desde los objetos de dominio.", size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.cards_column,
        ]
        self.refresh()

    def _formatear_restricciones_preview(self, restricciones: List[Restriccion]) -> str:
        """Formatea de forma matemática las primeras 3 restricciones del modelo."""
        partes: List[str] = []
        for r in restricciones[:3]:
            # Extracción limpia y segura desde los atributos de la entidad Restriccion
            terminos = " + ".join(
                f"{float(c):.4g}X{i+1}" 
                for i, c in enumerate(r.coeficientes) 
                if float(c) != 0.0
            ).replace("+ -", "- ")
            partes.append(f"{terminos} {r.signo.value} {float(r.rhs):.4g}")
            
        if len(restricciones) > 3:
            partes.append(f"... y {len(restricciones) - 3} restricciones más.")
            
        return "\n".join(partes)

    def _crear_tarjeta_problema(self, indice: int, problema: ProblemaPL) -> ft.Container:
        """Compone una tarjeta visual interactiva mapeando las propiedades OO del problema."""
        fo_algebraica = _formatear_funcion_objetivo_pedagogica(problema.tipo, problema.objetivo)
        badge_color = "#1d9e75" if problema.tipo == TipoOptimizacion.MAX else "#2563eb"

        return ft.Container(
            content=ft.Column([
                # Fila de Cabecera del Problema
                ft.Row([
                    ft.Row([
                        ft.Text(f"Problema #{indice+1}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        _badge_ui(problema.tipo.value, badge_color),
                        _badge_ui(f"{problema.total_variables} variables", "#374151"),
                        _badge_ui(f"{problema.total_restricciones} restricciones", "#374151"),
                    ], spacing=8),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                # Contenedor Visual de la Función Objetivo
                ft.Container(
                    content=ft.Text(
                        fo_algebraica, size=13, color=TEXT_PRIMARY, 
                        weight=ft.FontWeight.W_500, selectable=True
                    ),
                    padding=12,
                    bgcolor="#1e2130",
                    border_radius=8,
                    border=ft.Border(
                        top=ft.BorderSide(1, "#2a2d3a"), bottom=ft.BorderSide(1, "#2a2d3a"), 
                        left=ft.BorderSide(1, "#2a2d3a"), right=ft.BorderSide(1, "#2a2d3a")
                    ),
                ),

                # Contenedor Visual de las Desigualdades
                ft.Text(
                    self._formatear_restricciones_preview(problema.restricciones),
                    size=11, color=TEXT_MUTED,
                ),

                # Barra Lateral de Operaciones OO directas
                ft.Row([
                    _boton_accion_ui(
                        "Cargar y Activar", ft.Icons.UPLOAD, 
                        lambda _e: self._manejador_cargar_problema(indice)
                    ),
                    _boton_accion_ui(
                        "Clonar y Editar", ft.Icons.CONTENT_COPY,
                        lambda _e: self._manejador_clonar_y_editar(indice), color="#374151"
                    ),
                    _boton_accion_ui(
                        "Eliminar", ft.Icons.DELETE_OUTLINE,
                        lambda _e: self._manejador_eliminar_problema(indice), color="#7f1d1d"
                    ),
                ], spacing=8, wrap=True),
            ], spacing=10),
            padding=16,
            border_radius=12,
            bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), 
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
            ),
        )

    def refresh(self) -> None:
        """Consulta el Controlador y redibuja de forma reactiva las tarjetas del Canvas."""
        # Operación OO formal sobre el controlador: retorna List[ProblemaPL] de forma segura
        historial: List[ProblemaPL] = self.controlador.obtener_historial_completo()
        
        if not historial:
            self.cards_column.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, color=TEXT_MUTED, size=40),
                        ft.Text("No existen modelos registrados en el historial de sesión.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
                        ft.Text("Construye y valida un problema desde la ventana de ingreso para persistirlo.", color="#4a4f66", size=11, text_align=ft.TextAlign.CENTER),
                    ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=40,
                    border_radius=12,
                    bgcolor=BG_CARD,
                    border=ft.Border(
                        top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                        left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
                    ),
                    alignment=ft.alignment.Alignment(0, 0),
                )
            ]
        else:
            self.cards_column.controls = [
                self._crear_tarjeta_problema(i, p) for i, p in enumerate(historial)
            ]

    def _set_status_alert(self, mensaje: str, color_hex: str) -> None:
        """Pinta barras informativas contextuales sobre la ejecución de comandos."""
        icono = ft.Icons.CHECK_CIRCLE if color_hex == GREEN else (
            ft.Icons.DELETE if color_hex == RED else ft.Icons.INFO
        )
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

    def _manejador_cargar_problema(self, indice: int) -> None:
        """Actualiza el problema activo y redirige al usuario directo a la Solución Rápida."""
        # El método del controlador asigna de forma automática la propiedad .problema_activo
        self.controlador.obtener_problema_por_indice(indice)
        self._set_status_alert("✓ Modelo cargado como problema activo en la sesión.", GREEN)
        
        # Redirección MVC a través del callback formal inyectado de la NavigationApp (Índice 2: Vista General)
        if self.navegar_a:
            self.navegar_a(index=2)
        else:
            self.refresh()
            self.update()

    def _manejador_clonar_y_editar(self, indice: int) -> None:
        """Establece el problema seleccionado como activo y salta a la pantalla de edición."""
        self.controlador.obtener_problema_por_indice(indice)
        self._set_status_alert("✓ Modelo clonado. Puedes alterar sus celdas en la ventana de ingreso.", AMBER)
        
        # Redirección MVC hacia la Vista de Ingreso (Índice 0)
        if self.navegar_a:
            self.navegar_a(index=0)
        else:
            self.refresh()
            self.update()

    def _manejador_eliminar_problema(self, indice: int) -> None:
        """Purga la entidad inmutable del histórico de memoria."""
        # Remoción formal por índice; el controlador limpia el canvas activo si coincidían las instancias
        self.controlador.eliminar_problema_por_indice(indice)
        self.refresh()
        self._set_status_alert("✕ El problema seleccionado ha sido eliminado de la memoria.", RED)
        self.update()

    def build(self) -> ft.Control:
        self.refresh()
        return self
