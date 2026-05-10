from __future__ import annotations

from copy import deepcopy

import flet as ft
from pip._internal.models import index

from ui.estado_ui import get_problema_activo, set_problema_activo


ACCENT_COLOR = "#4b2981"


class VistaHistorial(ft.Column):
    """Vista de historial de problemas guardados.

    Hereda directamente de `ft.Column` para ser compatible con Flet 0.84.0.
    Renderiza una tarjeta por problema y permite cargar, clonar/editar y
    eliminar elementos del historial.
    """

    def __init__(self, controlador, navegar_a=None) -> None:
        super().__init__(expand=True, spacing=12, scroll=ft.ScrollMode.AUTO)
        self.controlador = controlador
        self.navegar_a = navegar_a

        self.cards_column = ft.Column(spacing=12, expand=True)
        self.status_text = ft.Text("", size=12)

        self.controls = [
            ft.Text("Historial de Problemas", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Consulta, carga, clona/edita o elimina problemas guardados en el historial.",
                size=12,
            ),
            ft.Divider(color="#404040"),
            self.cards_column,
            self.status_text,
        ]

        self.refresh()

    def _formatear_problema(self, problema: dict) -> list[ft.Control]:
        objetivo = problema.get("objetivo", []) or []
        restricciones = problema.get("restricciones", []) or []

        return [
            ft.Text(f"Tipo: {problema.get('tipo', 'MAX')}", weight=ft.FontWeight.BOLD),
            ft.Text(f"Objetivo: {objetivo}"),
            ft.Text(f"Restricciones: {len(restricciones)}"),
        ]

    def _crear_tarjeta(self, indice: int, problema: dict) -> ft.Control:
        snapshot = deepcopy(problema)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(f"Problema #{indice + 1}", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Text(snapshot.get("tipo", "MAX"), color="white", size=11),
                                    padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                    bgcolor=ACCENT_COLOR,
                                    border_radius=999,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        *self._formatear_problema(snapshot),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    content="Cargar",
                                    icon=ft.Icons.UPLOAD,
                                    style=ft.ButtonStyle(bgcolor=ACCENT_COLOR, color="white"),
                                    on_click=lambda _e: self._cargar_problema(deepcopy(snapshot)),
                                ),
                                ft.ElevatedButton(
                                    content="Clonar y Editar",
                                    icon=ft.Icons.CONTENT_COPY,
                                    style=ft.ButtonStyle(bgcolor="#404040", color="white"),
                                    on_click=lambda _e: self._clonar_y_editar(deepcopy(snapshot)),
                                ),
                                ft.OutlinedButton(
                                    content="Eliminar",
                                    icon=ft.Icons.DELETE,
                                    style=ft.ButtonStyle(color="#ff8a80"),
                                    on_click=lambda _e, idx=indice: self._eliminar_problema(idx),
                                ),
                            ],
                            wrap=True,
                            spacing=10,
                        ),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        )

    def refresh(self) -> None:
        historial = self.controlador.obtener_historial_de_problema() or []
        cards: list[ft.Control] = []

        if not historial:
            cards.append(
                ft.Container(
                    content=ft.Text(
                        "No hay problemas guardados todavía. Guarda un problema desde la vista de ingreso.",
                        italic=True,
                    ),
                    padding=20,
                    border_radius=12,
                    border=ft.Border.all(1, "#404040"),
                )
            )
        else:
            for indice, problema in enumerate(historial):
                cards.append(self._crear_tarjeta(indice, problema))

        self.cards_column.controls = cards

    def _cargar_problema(self, problema: dict) -> None:
        set_problema_activo(problema)
        setattr(self.controlador, "problema_activo", deepcopy(problema))
        self.status_text.value = "Problema cargado como problema activo."
        self.status_text.color = "#7ee081"

        if self.navegar_a is not None:
            self.navegar_a(deepcopy(problema), 2)
        else:
            self.update()

    def _clonar_y_editar(self, problema: dict) -> None:
        set_problema_activo(problema)
        setattr(self.controlador, "problema_activo", deepcopy(problema))
        self.status_text.value = "Problema clonado y enviado a la vista de ingreso para edición."
        self.status_text.color = "#7ee081"

        if self.navegar_a is not None:
            self.navegar_a(deepcopy(problema))
        else:
            self.update()

    def _eliminar_problema(self, indice: int) -> None:
        eliminado = self.controlador.operar_problema(None, 3, indice)
        if eliminado is not None and get_problema_activo() == eliminado:
            set_problema_activo(None)
            setattr(self.controlador, "problema_activo", None)

        self.refresh()
        self.status_text.value = "Problema eliminado del historial."
        self.status_text.color = "#ff8a80"
        self.update()

    def build(self) -> ft.Control:
        self.refresh()
        return self

