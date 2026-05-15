from __future__ import annotations

import flet as ft

from ui.estado_ui import get_problema_activo


ACCENT_COLOR = "#4b2981"


def _formatear_funcion_objetivo(tipo: str, objetivo: list) -> str:
    """Formatea la función objetivo como 'MAX Z = 2X1 + 3X2 - X3'."""
    if not objetivo:
        return f"{tipo} Z = 0"

    terminos = []
    for i, coef in enumerate(objetivo):
        try:
            c = float(coef)
        except (TypeError, ValueError):
            c = 0.0

        if c == 0:
            continue

        var_name = f"X{i + 1}"
        if c > 0:
            if not terminos:
                terminos.append(f"{c:.4g}{var_name}" if c != 1 else var_name)
            else:
                terminos.append(f"+ {c:.4g}{var_name}" if c != 1 else f"+ {var_name}")
        else:
            terminos.append(f"- {abs(c):.4g}{var_name}" if abs(c) != 1 else f"- {var_name}")

    expr = " ".join(terminos) if terminos else "0"
    return f"{tipo} Z = {expr}"


def _formatear_valor(valor) -> str:
    """Formatea un valor para presentación."""
    from fractions import Fraction

    if hasattr(valor, "item"):
        valor = valor.item()

    if isinstance(valor, Fraction):
        return str(valor)

    if isinstance(valor, float):
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")
        return texto if texto else "0"

    return str(valor)


class VistaGrafica(ft.Column):
    """Vista de Método Gráfico para problemas de 2 variables.

    Dibuja la región factible y el punto óptimo en el plano cartesiano.
    Muestra los resultados debajo del gráfico.
    """

    def __init__(self, controlador) -> None:
        super().__init__(expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador

        self.status_text = ft.Text("", size=12)
        self.img_container = ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=16,
            border=ft.Border.all(1, "#404040"),
            border_radius=12,
            expand=True,
        )
        self.resultado_container = ft.Column(spacing=10)

        self.controls = [
            ft.Text("Método Gráfico", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Visualización de la región factible para problemas de 2 variables.", size=12),
            ft.Divider(color="#404040"),
            self.resultado_container,
            ft.Divider(color="#404040"),
            self.status_text,
            self.img_container,
        ]

        self.refresh()

    def refresh(self) -> None:
        """Obtiene el problema activo y lo visualiza."""
        problema = getattr(self.controlador, "problema_activo", None) or get_problema_activo()

        if not problema:
            self.status_text.value = "Por favor, ingresa o selecciona un problema primero."
            self.status_text.color = "#ffb74d"
            self.img_container.content = ft.Container(
                content=ft.Text("No hay un problema activo disponible.", italic=True),
                padding=14,
                border=ft.Border.all(1, ACCENT_COLOR),
                border_radius=12,
            )
            self.resultado_container.controls = []
            self._safe_update()
            return

        # Validar que sea problema de 2 variables
        objetivo = problema.get("objetivo", []) or []
        num_vars = len(objetivo)

        if num_vars != 2:
            self.status_text.value = f"Método gráfico requiere exactamente 2 variables ({num_vars} detectadas)."
            self.status_text.color = "#ff8a80"
            self.img_container.content = ft.Container(
                content=ft.Text(
                    f"El Método Gráfico solo aplica para 2 variables.\n"
                    f"Este problema tiene {num_vars} variables.",
                    color="#ff8a80",
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=20,
                border=ft.Border.all(1, ACCENT_COLOR),
                border_radius=12,
            )
            self.resultado_container.controls = []
            self._safe_update()
            return

        # Resolver el problema
        resultado = self.controlador.resolver_LP(problema, 1)
        if not resultado:
            self.status_text.value = "Error al resolver el problema."
            self.status_text.color = "#ff8a80"
            self.img_container.content = ft.Text("Error de resolución.", color="#ff8a80")
            self.resultado_container.controls = []
            self._safe_update()
            return

        # ==========================================
        # PARCHE APLICADO BASADO EN LA AUDITORÍA
        # ==========================================
        estado = resultado.get("estado")

        if estado == 0:  # 0 es el código de éxito en ResolutorGeneral
            self.status_text.value = "Gráfico generado correctamente."
            self.status_text.color = "#7ee081"
            # Generar gráfico solo si hay solución óptima
            self._generar_grafico(problema, resultado)
        else:
            # Capturar mensaje de error ("inviable", "no acotado", etc.)
            mensaje_error = resultado.get("mensaje", "El problema no tiene una solución óptima acotada.")
            self.status_text.value = f"Atención: {mensaje_error}"
            self.status_text.color = "#ffb74d"  # Color de advertencia (naranja)

            # Limpiar la imagen y mostrar el cuadro de advertencia
            self.img_container.content = ft.Container(
                content=ft.Text(
                    f"No se puede dibujar la región óptima:\n{mensaje_error}",
                    color="#ffb74d",
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_500,
                ),
                padding=20,
                border=ft.Border.all(1, "#ffb74d"),
                border_radius=12,
            )
            # Renderizamos la caja de resultados para que el usuario lea el estatus detallado (mostrará N/D)
            self._renderizar_resultados(problema, resultado)

        self._safe_update()

    def _generar_grafico(self, problema: dict, resultado: dict) -> None:
        """Genera y renderiza el gráfico cartesiano + resultados."""
        try:
            from src.utils.graficador import generar_grafico_cartesiano

            img_b64 = generar_grafico_cartesiano(problema, resultado)
            if img_b64:
                self.img_container.content = ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN)
            else:
                self.img_container.content = ft.Text("Error al generar gráfico.", color="#ff8a80")

            # Renderizar resultados como en vista_matricial
            self._renderizar_resultados(problema, resultado)

        except Exception as e:
            self.img_container.content = ft.Container(
                content=ft.Text(f"Error: {str(e)[:100]}", color="#ff8a80", size=10),
                padding=14,
                border=ft.Border.all(1, "#ff8a80"),
                border_radius=12,
            )
            self.resultado_container.controls = []

    def _renderizar_resultados(self, problema: dict, resultado: dict) -> None:
        """Presenta los resultados en el mismo formato que vista_matricial."""
        tipo = problema.get("tipo", "MAX")
        objetivo = problema.get("objetivo", [])
        func_objetivo = _formatear_funcion_objetivo(tipo, objetivo)

        # Extraer datos según la estructura real del backend
        z_optimo = _formatear_valor(resultado.get("valor_z", "N/D"))
        variables = resultado.get("variables", []) or []
        mensaje = resultado.get("mensaje", "")

        self.resultado_container.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text(func_objetivo, weight=ft.FontWeight.BOLD, size=14, selectable=True),
                    ft.Text(f"Z óptimo: {z_optimo}", weight=ft.FontWeight.W_600),
                    ft.Text(
                        "Variables: "
                        + ",  ".join([f"X{i + 1} = {_formatear_valor(v)}" for i, v in enumerate(variables)])
                    ),
                    ft.Text(mensaje, italic=True, size=11),
                ], spacing=8),
                padding=14,
                border=ft.Border.all(1, ACCENT_COLOR),
                border_radius=12,
            )
        ]

    def _safe_update(self) -> None:
        """Actualiza la vista de forma segura."""
        try:
            if self.page is not None:
                self.update()
        except RuntimeError:
            pass

    def build(self) -> ft.Control:
        return self