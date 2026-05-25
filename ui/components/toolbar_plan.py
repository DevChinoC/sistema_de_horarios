"""
Componente UI: ToolbarPlan

Cabecera con título del plan, botón volver y botones de exportación PDF.
Extraído de DetallePlanView.

SOLO UI: no contiene lógica de negocio.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes


class ToolbarPlan(ft.Container):
    """Barra superior de la vista de detalle de plan.

    Incluye:
    - Botón de volver (flecha izquierda).
    - Nombre del plan.
    - Botones Visualizar y Descargar PDF (opcionales).

    Uso:
        toolbar = ToolbarPlan(
            nombre_plan="Ingeniería 2024",
            on_volver=lambda: ...,
            on_visualizar=lambda: ...,
            on_descargar=lambda: ...,
        )
    """

    def __init__(
        self,
        nombre_plan: str,
        on_volver: Callable,
        on_visualizar: Callable | None = None,
        on_descargar: Callable | None = None,
    ) -> None:
        botones_pdf: list[ft.Control] = []

        if on_visualizar:
            botones_pdf.append(
                ft.OutlinedButton(
                    text="Visualizar documento",
                    icon=ft.Icons.DESCRIPTION_OUTLINED,
                    icon_color=Colores.AZUL_PRIMARIO,
                    on_click=lambda _: on_visualizar(),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.padding.symmetric(horizontal=20, vertical=10),
                        side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                        color=Colores.AZUL_PRIMARIO,
                        text_style=ft.TextStyle(size=13, font_family=Fuentes.BOTONES),
                    ),
                )
            )

        if on_descargar:
            botones_pdf.append(
                ft.ElevatedButton(
                    text="Descargar",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda _: on_descargar(),
                    bgcolor=Colores.AZUL_PRIMARIO,
                    color=Colores.BLANCO,
                    elevation=0,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.padding.symmetric(horizontal=30, vertical=10),
                        text_style=ft.TextStyle(size=13, font_family=Fuentes.BOTONES),
                    ),
                )
            )

        content_row = ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=Colores.AZUL_PRIMARIO,
                    icon_size=20,
                    on_click=lambda _: on_volver(),
                    tooltip="Volver",
                ),
                ft.Text(
                    f"Plan de estudios - {nombre_plan}",
                    size=20,
                    weight=ft.FontWeight.W_400,
                    color=Colores.TEXTO,
                    font_family=Fuentes.TITULO,
                    expand=True,
                ),
                *botones_pdf,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(left=16, top=10, bottom=2, right=16),
            content=content_row,
        )
