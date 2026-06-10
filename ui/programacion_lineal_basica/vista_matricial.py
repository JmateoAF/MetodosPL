"""
vista_matricial.py
==================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Responsable del renderizado paso a paso de los solucionadores algebraicos
tabulares (Simplex, Gran M y Dos Fases).

Responsabilidades:
    - Interpretar colecciones inmutables de IteracionTabular.
    - Renderizar los DataTables algebraicos formateando celdas complejas.
    - Utilizar el LocalizadorUI para iluminar el cruce de fila/columna pivote.
    - Utilizar el AnalizadorMatematico para procesar variables Big M y fracciones.

Autor: UI Matrix View Module — MVC Linear Optimizer
"""

from __future__ import annotations
from typing import List, Optional
import flet as ft

# Importaciones estrictas de la capa de Dominio y Control del Sistema
from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal.respuesta import RespuestaTabularPL, IteracionTabular

# Importaciones utilitarias para procesamiento geométrico y visual
from src.utils.programacion_lineal_basica.herramientas_calculo import AnalizadorMatematico
from src.utils.programacion_lineal_basica.localizador_ui import LocalizadorUI

# Paleta de colores institucional para mantener la consistencia estética
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BG_TABLE: str = "#0d0f1a"
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


class VistaMatricial(ft.Column):
    """
    Vista modular encargada del desglose analítico iteración por iteración 
    de las matrices algebraicas resueltas por el motor matemático.
    """

    def __init__(self, controlador, opcion_resolucion: int, titulo: str, descripcion: str) -> None:
        # Inicialización nativa de la estructura Column de Flet v0.85
        super().__init__(expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.opcion_resolucion: int = opcion_resolucion
        self.titulo: str = titulo
        self.descripcion: str = descripcion

        # Contenedores dinámicos del Layout reactivo
        self.status_row: ft.Row = ft.Row([], visible=False)
        self.resultados_column: ft.Column = ft.Column(spacing=14)

        # Configuración del esqueleto estático de la ventana
        self.controls = [
            ft.Column([
                ft.Text(self.titulo, size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text(self.descripcion, size=12, color=TEXT_MUTED),
            ], spacing=2),
            ft.Divider(color=BORDER_COLOR, height=1),
            self.status_row,
            self.resultados_column,
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
                padding=14, border_radius=8, bgcolor=color_hex + "18",
                border=ft.Border(
                    top=ft.BorderSide(1, color_hex + "44"), bottom=ft.BorderSide(1, color_hex + "44"),
                    left=ft.BorderSide(1, color_hex + "44"), right=ft.BorderSide(1, color_hex + "44")
                ),
            )
        ]

    def _crear_tabla_visual(self, iteracion: IteracionTabular) -> ft.Control:
        """
        Construye una instancia ft.DataTable inyectando los datos algebraicos.
        Aprovecha las utilidades POO para iluminar pivotes y limpiar fracciones.
        """
        # Extraer dimensiones y datos base de la entidad inmutable
        filas_matriz = iteracion.tabla.tolist()
        encabezado = iteracion.encabezados
        
        # Bandera de formato: Si el método seleccionado es M Grande (3), activamos la decodificación de M
        evaluar_gran_m = (self.opcion_resolucion == 3)

        if not filas_matriz:
            return ft.Container(
                content=ft.Text("Iteración sin matriz de datos.", color=TEXT_MUTED, italic=True),
                padding=12, border_radius=10, bgcolor=BG_CARD,
                border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            )

        # 1. Armado de Columnas del DataTable
        columns = [
            ft.DataColumn(ft.Text(str(col), weight=ft.FontWeight.BOLD, size=12, color="white"))
            for col in encabezado
        ]

        # 2. Armado de Filas Celda por Celda
        rows = []
        for idx_fila, fila_datos in enumerate(filas_matriz):
            cells = []
            
            for idx_col, valor_crudo in enumerate(fila_datos):
                # Aplicamos el purificador funcional de fracciones exactas / notación "M"
                texto_valor = AnalizadorMatematico.formatear_valor_pedagogico(valor_crudo, evaluar_m=evaluar_gran_m)
                
                # Definición de estilo base
                color_texto = TEXT_PRIMARY
                peso_texto = ft.FontWeight.NORMAL
                bg_celda = None

                # Control estético especial para la columna Cero (Variables Básicas)
                if idx_col == 0:
                    peso_texto = ft.FontWeight.BOLD
                    color_texto = BLUE if idx_fila == 0 else GREEN

                # Validación topológica del pivote interceptado
                es_pivote = LocalizadorUI.es_celda_pivote(iteracion, idx_fila, idx_col)
                if es_pivote:
                    color_texto = "white"
                    peso_texto = ft.FontWeight.BOLD
                    bg_celda = AMBER + "44"  # Iluminación de celda en intersección

                # Construcción del Control Textual
                texto_ui = ft.Text(texto_valor, size=12, color=color_texto, weight=peso_texto)
                
                # Si es pivote, se recubre con un contenedor para iluminar el background
                if bg_celda:
                    content_celda = ft.Container(content=texto_ui, bgcolor=bg_celda, padding=4, border_radius=4)
                else:
                    content_celda = texto_ui

                cells.append(ft.DataCell(content_celda))
            
            # Decoración de la Fila Objetivo (Z o W, índice 0)
            es_fila_objetivo = (idx_fila == 0)
            color_fila_base = ACCENT_COLOR + "33" if es_fila_objetivo else None
            
            rows.append(ft.DataRow(
                cells=cells,
                color={"": color_fila_base} if color_fila_base else {"": BG_TABLE},
            ))

        tabla_control = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "55"), bottom=ft.BorderSide(1, ACCENT_COLOR + "55"), left=ft.BorderSide(1, ACCENT_COLOR + "55"), right=ft.BorderSide(1, ACCENT_COLOR + "55")),
            heading_row_color={"": ACCENT_COLOR},
            data_row_color={"": BG_TABLE}, 
            heading_row_height=42,
            data_row_max_height=44,
            data_row_min_height=40,
            horizontal_margin=12,
            column_spacing=20,
            divider_thickness=0.5,
        )

        return ft.Container(
            content=ft.Row([tabla_control], scroll=ft.ScrollMode.AUTO),
            padding=12, border_radius=10, bgcolor=BG_TABLE,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
        )

    def _renderizar_paneles_resultados(self, resultado: RespuestaTabularPL, problema: ProblemaPL) -> List[ft.Control]:
        """Procesa y mapea el listado de Iteraciones Tabulares inmutables de la respuesta."""
        controles: List[ft.Control] = []

        # 1. Panel Superior (Cabecera y Resumen Óptimo)
        fo_str = _formatear_funcion_objetivo_ui(problema.tipo, problema.objetivo)
        
        # Mapeo funcional de la respuesta numérica del estado final
        variables = resultado.variables_decision or []
        z_val = AnalizadorMatematico.formatear_valor_pedagogico(resultado.z_optimo) if resultado.z_optimo is not None else "N/D"
        
        texto_vars = ", ".join(f"X{i+1} = {AnalizadorMatematico.formatear_valor_pedagogico(v)}" for i, v in enumerate(variables)) if variables else "N/D"

        controles.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Z óptimo (Matricial)", size=10, color=TEXT_MUTED),
                                ft.Text(z_val, size=18, color=GREEN, weight=ft.FontWeight.BOLD),
                            ], spacing=2),
                            padding=16, border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Variables Evaluadas", size=10, color=TEXT_MUTED),
                                ft.Text(texto_vars, size=13, color=TEXT_PRIMARY),
                            ], spacing=2),
                            padding=16, border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        ),
                    ], spacing=8, wrap=True),
                    ft.Text(f"Motivo de parada: {resultado.estado.value}", size=11, color=TEXT_MUTED, italic=True),
                ], spacing=10),
                padding=16, border_radius=12, bgcolor=BG_CARD,
                border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
            )
        )

        # 2. Despliegue Secuencial de Tableaus
        if not resultado.iteraciones:
            return controles

        for idx, iteracion in enumerate(resultado.iteraciones, start=1):
            fase_num = iteracion.fase
            msg_iter = iteracion.mensaje

            # Construcción Inteligente del Título de la Iteración
            componentes_titulo = [ft.Text(f"Iteración {idx}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)]
            
            if fase_num is not None:
                color_fase = "#1d9e75" if fase_num == 1 else "#2563eb"
                componentes_titulo.append(
                    ft.Container(
                        content=ft.Text(f"Fase {fase_num}", size=10, color="white", weight=ft.FontWeight.W_600),
                        padding=8, bgcolor=color_fase, border_radius=99,
                    )
                )

            controles.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row(componentes_titulo, spacing=8),
                        ft.Text(msg_iter, size=12, color=TEXT_MUTED) if msg_iter else ft.Container(),
                        self._crear_tabla_visual(iteracion),
                    ], spacing=10),
                    padding=16, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                )
            )

        return controles

    def refresh(self) -> None:
        """Ejecuta el ciclo de carga y resolución para la UI conectándose al Controlador."""
        self.resultados_column.controls.clear()
        
        # Invocación OO de lectura directa de estado
        problema: Optional[ProblemaPL] = self.controlador.problema_activo

        if problema is None:
            self._mostrar_alerta_status("Ingresa o selecciona un problema matemático primero.", AMBER, ft.Icons.INFO_OUTLINE)
            self.resultados_column.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.TABLE_CHART, color=TEXT_MUTED, size=48),
                        ft.Text("Sin modelo activo en la sesión.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
                    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=48, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)), alignment=ft.alignment.Alignment(0, 0),
                )
            ]
            self._safe_update_ui()
            return

        # Resolución mediante el Controlador (Simplex, Gran M o Dos Fases)
        resultado: Optional[RespuestaTabularPL] = self.controlador.resolver_LP(problema, self.opcion_resolucion)
        
        if resultado is None:
            self._mostrar_alerta_status("El motor matemático interrumpió el proceso inesperadamente.", RED)
            self.resultados_column.controls = [
                ft.Container(
                    content=ft.Text("Excepción en la obtención de resultados algebraicos.", color=RED),
                    padding=16, border_radius=12, bgcolor=BG_CARD,
                    border=ft.Border(top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"), left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44")),
                )
            ]
            self._safe_update_ui()
            return

        # Traducción semántica del estado inmutable
        if resultado.estado == EstadoProblema.OPTIMO:
            self._mostrar_alerta_status("Proceso concluido. Óptimo alcanzado.", GREEN)
        elif resultado.estado == EstadoProblema.REQUIERE_OTRO_METODO:
            self._mostrar_alerta_status("Desajuste de algoritmo: Las restricciones del modelo no encajan con este método.", AMBER)
        else:
            self._mostrar_alerta_status(f"Conclusión anormal: {resultado.estado.name}", AMBER)

        self.resultados_column.controls = self._renderizar_paneles_resultados(resultado, problema)
        self._safe_update_ui()

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