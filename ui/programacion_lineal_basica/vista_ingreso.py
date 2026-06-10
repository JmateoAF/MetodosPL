# ui/vista_ingreso.py
"""
vista_ingreso.py
================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Implementa un entorno flexible de entrada de datos para modelos de PL.

Secciones del Layout:
    1. Región Superior Fija: Control de modo (Tradicional, Natural, CSV).
    2. Región Central con Scroll: Formularios dinámicos e inputs de texto.
    3. Región Inferior Fija: Botones de control y persistencia del Dominio.

Autor: UI Input View Module — MVC Linear Optimizer
"""

from __future__ import annotations
from typing import List, Optional, cast
import flet as ft

# Importaciones estrictas de las capas de Dominio y Utilidades del Sistema
from src.models.entity.programacion_lineal.enums import TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
from src.utils.programacion_lineal_basica.parser import MotorParsing

# Paleta de colores institucional para mantener la consistencia estética neon/oscura
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BG_FIELD: str = "#1e2130"
BORDER_COLOR: str = "#2a2d3a"
TEXT_MUTED: str = "#6b7280"
TEXT_PRIMARY: str = "#f0f0f0"
GREEN: str = "#1d9e75"
AMBER: str = "#f6ad55"
RED: str = "#ef645f"


def _crear_campo_ui(label: str, valor: str = "") -> ft.TextField:
    """Factory function para generar campos de texto estandarizados."""
    return ft.TextField(
        label=label,
        value=str(valor),
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


def _crear_boton_ui(texto: str, icono: ft.Icons, on_click, color: Optional[str] = None) -> ft.ElevatedButton:
    """Factory function para generar botones con iconografía homogénea."""
    bg_color = color if color is not None else ACCENT_COLOR
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(cast(ft.IconData, icono), size=15, color="white"),
                ft.Text(texto, size=12, color="white")
            ],
            tight=True,
            spacing=6,
        ),
        bgcolor=bg_color,
        on_click=on_click,
    )


class VistaIngreso(ft.Container):
    """
    Vista modular encargada de capturar, validar y empaquetar un problema de 
    programación lineal hacia la capa del controlador.
    """

    def __init__(self, controlador, navegar_a=None) -> None:
        super().__init__(expand=True, padding=0, bgcolor="transparent")
        self.controlador = controlador
        self.navegar_a = navegar_a

        # --- Variables de Estado de la UI ---
        self.modo_ingreso_actual: int = 0  # 0: Tradicional, 1: Natural, 2: CSV
        self.status_text: ft.Text = ft.Text("", size=12, visible=False)

        # --- Controles del Modo Tradicional (Matricial) ---
        self.tipo_dropdown: ft.Dropdown = ft.Dropdown(
            label="Optimización",
            value="MAX",
            options=[ft.dropdown.Option("MAX"), ft.dropdown.Option("MIN")],
            width=160,
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            border_radius=8,
        )
        self.campos_objetivo_ui: List[ft.TextField] = []
        self.filas_restricciones_ui: List[dict] = []

        # --- Controles de los Modos Avanzados de Parsing (Natural / CSV) ---
        self.input_objetivo_avanzado: ft.TextField = ft.TextField(
            label="Función Objetivo Cruda",
            hint_text="Ej: Max Z = 3x1 + 5x2  o  Max, 3, 5",
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            border_radius=8,
        )
        self.input_restricciones_avanzado: ft.TextField = ft.TextField(
            label="Líneas de Restricciones (Una por fila)",
            hint_text="Ej: 2x1 + x2 <= 10\nEj: 2, 1, <=, 10",
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            border_radius=8,
            multiline=True,
            min_lines=4,
        )

        # --- Contenedor Principal Central del Layout (Área de Scroll) ---
        self.scrollable_body_container: ft.Container = ft.Container(expand=True, padding=0)

        # Inicialización estructural de datos y dibujo de la vista
        self._inicializar_formulario_tradicional()
        self._conmutar_cuerpo_central()
        self.content = self._inicializar_layout_estructural()

    # ══════════════════════════════════════════════════════════════════
    # SECCIÓN 1: COMPONENTE SUPERIOR FIJO (SELECCIÓN DE MODO)
    # ══════════════════════════════════════════════════════════════════

    def _inicializar_barra_modos(self) -> ft.Container:
        """Construye las pestañas de selección de entrada."""
        def _on_tab_click(e: ft.ControlEvent, index_modo: int) -> None:
            self.modo_ingreso_actual = index_modo
            self._conmutar_cuerpo_central()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text("Formato de Ingreso:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                    ft.ElevatedButton(
                        "Tradicional por Celdas",
                        bgcolor=ACCENT_COLOR if self.modo_ingreso_actual == 0 else "#374151",
                        color="white",
                        on_click=lambda e: _on_tab_click(e, 0)
                    ),
                    ft.ElevatedButton(
                        "Lenguaje Natural (Algebraico)",
                        bgcolor=ACCENT_COLOR if self.modo_ingreso_actual == 1 else "#374151",
                        color="white",
                        on_click=lambda e: _on_tab_click(e, 1)
                    ),
                    ft.ElevatedButton(
                        "Coeficientes planos (CSV)",
                        bgcolor=ACCENT_COLOR if self.modo_ingreso_actual == 2 else "#374151",
                        color="white",
                        on_click=lambda e: _on_tab_click(e, 2)
                    ),
                ],
                spacing=8
            ),
            padding=12,
            border_radius=12,
            bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR),
                bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR),
                right=ft.BorderSide(1, BORDER_COLOR),
            ),
        )

    # ══════════════════════════════════════════════════════════════════
    # SECCIÓN 2: CUERPO DINÁMICO (FORMULARIOS CON SCROLL)
    # ══════════════════════════════════════════════════════════════════

    def _inicializar_formulario_tradicional(self) -> None:
        """Carga el estado inicial de dos variables y una restricción estándar."""
        self.campos_objetivo_ui = [_crear_campo_ui("X1"), _crear_campo_ui("X2")]
        self.filas_restricciones_ui = [self._crear_estructura_fila_restriccion(0)]

    def _crear_estructura_fila_restriccion(self, indice_fila: int) -> dict:
        """Genera los controles visuales correspondientes a una fila de restricción."""
        campos_coeficientes = [_crear_campo_ui(f"X{i+1}") for i in range(len(self.campos_objetivo_ui))]
        return {
            "indice": indice_fila,
            "coeficientes": campos_coeficientes,
            "signo": ft.Dropdown(
                value="<=",
                options=[ft.dropdown.Option("<="), ft.dropdown.Option(">="), ft.dropdown.Option("==")],
                width=90,
                border_color=BORDER_COLOR,
                focused_border_color=ACCENT_COLOR,
                bgcolor=BG_FIELD,
                color=TEXT_PRIMARY,
                border_radius=8,
            ),
            "rhs": _crear_campo_ui("RHS"),
        }

    def _renderizar_bloque_contenedor(self, titulo: str, contenido: ft.Control) -> ft.Container:
        """Encapsula una subsección del formulario dentro de una tarjeta visual."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    contenido,
                ],
                spacing=12
            ),
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

    def _conmutar_cuerpo_central(self) -> None:
        """Intercambia el contenido del área central según el modo activo."""
        if self.modo_ingreso_actual == 0:
            # --- RENDER MODO TRADICIONAL POR CELDAS ---
            controles_fo = [ft.Text("Z =", color=TEXT_MUTED, size=13)]
            for idx, campo in enumerate(self.campos_objetivo_ui):
                controles_fo.append(campo)
                if idx < len(self.campos_objetivo_ui) - 1:
                    controles_fo.append(ft.Text("+", color=TEXT_MUTED, size=14))

            tarjeta_fo = self._renderizar_bloque_contenedor(
                "Función Objetivo",
                ft.Column(
                    [
                        self.tipo_dropdown,
                        ft.Row(controles_fo, wrap=True, spacing=6),
                        ft.Row(
                            [
                                _crear_boton_ui("Añadir variable", ft.Icons.ADD, self._accion_agregar_variable),
                                _crear_boton_ui("Eliminar variable", ft.Icons.REMOVE, self._accion_eliminar_variable, color="#374151"),
                            ],
                            spacing=8
                        ),
                    ],
                    spacing=10
                )
            )

            columna_restricciones = ft.Column(spacing=10)
            for posicion, fila in enumerate(self.filas_restricciones_ui, start=1):
                controles_fila = []
                for j, campo_coef in enumerate(fila["coeficientes"]):
                    controles_fila.append(campo_coef)
                    if j < len(fila["coeficientes"]) - 1:
                        controles_fila.append(ft.Text("+", color=TEXT_MUTED, size=12))
                
                bloque_fila = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(f"Restricción {posicion}", size=12, weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
                            ft.Row(controles_fila + [fila["signo"], fila["rhs"]], wrap=True, spacing=6),
                        ],
                        spacing=8
                    ),
                    padding=12, border_radius=10, bgcolor="#12141f",
                    border=ft.Border(
                        top=ft.BorderSide(1, "#252836"), bottom=ft.BorderSide(1, "#252836"),
                        left=ft.BorderSide(1, "#252836"), right=ft.BorderSide(1, "#252836")
                    )
                )
                columna_restricciones.controls.append(bloque_fila)

            columna_restricciones.controls.append(
                ft.Row(
                    [
                        _crear_boton_ui("Añadir restricción", ft.Icons.ADD_CIRCLE_OUTLINE, self._accion_agregar_restriccion),
                        _crear_boton_ui("Eliminar restricción", ft.Icons.REMOVE_CIRCLE_OUTLINE, self._accion_eliminar_restriccion, color="#374151"),
                    ],
                    spacing=8
                )
            )
            tarjeta_restricciones = self._renderizar_bloque_contenedor("Restricciones Lineales", columna_restricciones)

            self.scrollable_body_container.content = ft.Column([tarjeta_fo, tarjeta_restricciones], spacing=16)

        else:
            # --- RENDER MODOS AVANZADOS (NATURAL / CSV) ---
            titulo_seccion = "Ingreso en Formato Algebraico Natural" if self.modo_ingreso_actual == 1 else "Ingreso en Formato Coeficientes CSV"
            self.input_objetivo_avanzado.label = "Escribe la Función Objetivo" if self.modo_ingreso_actual == 1 else "Ingresa los Coeficientes Objetivo por comas"
            self.input_restricciones_avanzado.label = "Escribe las Restricciones (Una por línea)" if self.modo_ingreso_actual == 1 else "Ingresa las Restricciones CSV (Una por línea)"

            tarjeta_avanzada = self._renderizar_bloque_contenedor(
                titulo_seccion,
                ft.Column(
                    [
                        self.input_objetivo_avanzado,
                        self.input_restricciones_avanzado
                    ],
                    spacing=14
                )
            )
            self.scrollable_body_container.content = tarjeta_avanzada

        self.update()

    # ══════════════════════════════════════════════════════════════════
    # SECCIÓN 3: BARRA INFERIOR FIJA (ACCIONES Y GUARDADO)
    # ══════════════════════════════════════════════════════════════════

    def _inicializar_layout_estructural(self) -> ft.Container:
        """Compone la distribución final dividiendo la pantalla en las 3 zonas solicitadas."""
        barra_modos_superior = self._inicializar_barra_modos()

        cabecera_informativa = ft.Column(
            [
                ft.Text("Configuración del Modelo Lineal", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Digita los parámetros del problema usando el formato que te sea más cómodo.", size=12, color=TEXT_MUTED),
            ],
            spacing=2
        )

        barra_botones_inferior = ft.Row(
            [
                _crear_boton_ui("Guardar y Activar Problema", ft.Icons.SAVE, self._manejador_guardar_problema, color=GREEN),
                _crear_boton_ui("Vaciar Campos", ft.Icons.REFRESH, self._manejador_vaciar_valores, color="#374151"),
                _crear_boton_ui("Reiniciar Estructura", ft.Icons.RESTART_ALT, self._manejador_restablecer_todo, color="#374151"),
            ],
            spacing=8,
            wrap=True
        )

        # Región central envuelta en un Scroll dinámico aislado
        cuerpo_con_scroll = ft.Column(
            [self.scrollable_body_container],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        return ft.Container(
            content=ft.Column(
                [
                    barra_modos_superior,
                    cabecera_informativa,
                    ft.Divider(color=BORDER_COLOR, height=1),
                    cuerpo_con_scroll,
                    ft.Divider(color=BORDER_COLOR, height=1),
                    barra_botones_inferior,
                    self.status_text,
                ],
                spacing=16,
                expand=True
            ),
            expand=True,
        )

    # ══════════════════════════════════════════════════════════════════
    # ACCIONES LOGÍSTICAS DE COMPONENTES TRADICIONALES
    # ══════════════════════════════════════════════════════════════════

    def _accion_agregar_variable(self, _e) -> None:
        nueva_pos = len(self.campos_objetivo_ui) + 1
        self.campos_objetivo_ui.append(_crear_campo_ui(f"X{nueva_pos}"))
        for fila in self.filas_restricciones_ui:
            fila["coeficientes"].append(_crear_campo_ui(f"X{nueva_pos}"))
        self._conmutar_cuerpo_central()

    def _accion_eliminar_variable(self, _e) -> None:
        if len(self.campos_objetivo_ui) > 1:
            self.campos_objetivo_ui.pop()
            for fila in self.filas_restricciones_ui:
                if fila["coeficientes"]:
                    fila["coeficientes"].pop()
            self._conmutar_cuerpo_central()
        else:
            self._mostrar_mensaje_status("Operación inválida: El modelo debe tener al menos una variable.", RED)

    def _accion_agregar_restriccion(self, _e) -> None:
        self.filas_restricciones_ui.append(self._crear_estructura_fila_restriccion(len(self.filas_restricciones_ui)))
        self._conmutar_cuerpo_central()

    def _accion_eliminar_restriccion(self, _e) -> None:
        if len(self.filas_restricciones_ui) > 1:
            self.filas_restricciones_ui.pop()
            self._conmutar_cuerpo_central()
        else:
            self._mostrar_mensaje_status("Operación inválida: El modelo debe tener al menos una restricción.", RED)

    # ══════════════════════════════════════════════════════════════════
    # COMPILACIÓN, VALIDACIÓN Y PARSING CON ENFOQUE POO
    # ══════════════════════════════════════════════════════════════════

    def _compilar_modo_tradicional_a_objeto(self) -> ProblemaPL:
        """Construye un objeto ProblemaPL leyendo los inputs numéricos de las celdas."""
        def _parsear_texto_a_primitivo(valor_crudo: str) -> float:
            texto = valor_crudo.strip().replace(",", ".")
            if not texto:
                return 0.0
            if "/" in texto:
                from fractions import Fraction
                return float(Fraction(texto))
            return float(texto)

        tipo_enum = TipoOptimizacion(self.tipo_dropdown.value)
        vector_objetivo = [_parsear_texto_a_primitivo(c.value) for c in self.campos_objetivo_ui]

        lista_restricciones: List[Restriccion] = []
        for fila in self.filas_restricciones_ui:
            coefs = [_parsear_texto_a_primitivo(c.value) for c in fila["coeficientes"]]
            signo_enum = SignoRestriccion(fila["signo"].value)
            rhs_val = _parsear_texto_a_primitivo(fila["rhs"].value)

            lista_restricciones.append(Restriccion(coeficientes=coefs, signo=signo_enum, rhs=rhs_val))

        return ProblemaPL(tipo=tipo_enum, objetivo=vector_objetivo, restricciones=lista_restricciones)

    def _manejador_guardar_problema(self, _e) -> None:
        """Manejador del botón de guardado. Aplica el parsing u objetos e interactúa con el Controlador."""
        try:
            problema_entidad: Optional[ProblemaPL] = None

            if self.modo_ingreso_actual == 0:
                # Caso 0: Lectura directa de campos estructurados
                problema_entidad = self._compilar_modo_tradicional_a_objeto()
            else:
                # Casos 1 y 2: Delegación del stream de texto al Motor de Parsing
                texto_obj = self.input_objetivo_avanzado.value.strip()
                lineas_res = self.input_restricciones_avanzado.value.split("\n")

                if self.modo_ingreso_actual == 1:
                    problema_entidad = MotorParsing.natural_a_entidades(texto_obj, lineas_res)
                else:
                    problema_entidad = MotorParsing.csv_a_entidades(texto_obj, lineas_res)

            # Inyección limpia al flujo del Controlador
            if problema_entidad is not None:
                self.controlador.ingresar_problema(problema_entidad)
                self._mostrar_mensaje_status("✓ Problema matemáticamente validado, guardado y activado con éxito.", GREEN)
            else:
                raise ValueError("Estructura de datos nula generada.")

        except Exception as error_capturado:
            # Las validaciones del constructor de los modelos brotan aquí de forma segura
            self._mostrar_mensaje_status(f"✗ Error de Validación: {error_capturado}", RED)

    # ══════════════════════════════════════════════════════════════════
    # MANEJADORES DE BORRADO Y LIMPIEZA DE PANTALLA
    # ══════════════════════════════════════════════════════════════════

    def _manejador_vaciar_valores(self, _e) -> None:
        """Limpia el texto de los inputs sin deformar el esqueleto visual de la pestaña."""
        if self.modo_ingreso_actual == 0:
            for campo in self.campos_objetivo_ui:
                campo.value = ""
            for fila in self.filas_restricciones_ui:
                for campo_coef in fila["coeficientes"]:
                    campo_coef.value = ""
                fila["rhs"].value = ""
        else:
            self.input_objetivo_avanzado.value = ""
            self.input_restricciones_avanzado.value = ""
            
        self._mostrar_mensaje_status("Campos vaciados.", AMBER)
        self._conmutar_cuerpo_central()

    def _manejador_restablecer_todo(self, _e) -> None:
        """Reinicia la ventana a su configuración canónica de desarrollo."""
        self.tipo_dropdown.value = "MAX"
        self.input_objetivo_avanzado.value = ""
        self.input_restricciones_avanzado.value = ""
        self._inicializar_formulario_tradicional()
        self._mostrar_mensaje_status("Estructura reseteada por completo.", AMBER)
        self._conmutar_cuerpo_central()

    def _mostrar_mensaje_status(self, mensaje: str, color_hex: str) -> None:
        """Muestra alertas contextuales e hilos de ejecución en el pie de la vista."""
        self.status_text.value = mensaje
        self.status_text.color = color_hex
        self.status_text.visible = True
        self.update()

    def build(self) -> ft.Control:
        return self