"""
Componente UI: DialogConflictos

Diálogo modal que muestra conflictos de horario de forma amigable.
Extrae la lógica de diálogo de error de la view principal.

SOLO UI: recibe datos ya procesados, no valida nada.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes


class DialogConflictos(ft.AlertDialog):
    """Diálogo que muestra un mensaje de conflicto de horario.

    Uso:
        dlg = DialogConflictos(
            mensaje="El horario Lunes 07:00-09:00 colisiona con tronco.",
            conflictos=[{"dia": "Lunes", "hora_inicio": "07:00", "hora_fin": "09:00"}],
        )
        page.open(dlg)
    """

    def __init__(
        self,
        mensaje: str,
        conflictos: list[dict] | None = None,
        on_cerrar: Callable | None = None,
    ) -> None:
        detalles: list[ft.Control] = [
            ft.Text(
                mensaje,
                size=13,
                color=Colores.TEXTO,
                font_family=Fuentes.CAMPOS,
            )
        ]

        if conflictos:
            detalles.append(ft.Container(height=8))
            detalles.append(ft.Text(
                "Conflictos detectados:",
                size=12,
                weight=ft.FontWeight.W_600,
                color=Colores.TEXTO,
                font_family=Fuentes.CAMPOS,
            ))
            for c in conflictos:
                detalles.append(
                    ft.Container(
                        content=ft.Text(
                            f"• {c.get('dia', '')}  "
                            f"{c.get('hora_inicio', '')} – {c.get('hora_fin', '')}",
                            size=12,
                            color=Colores.ROJO,
                            font_family=Fuentes.CAMPOS,
                        ),
                        padding=ft.padding.only(left=12, top=2),
                    )
                )

        def _cerrar(e):
            if self.page:
                self.page.close(self)
            if on_cerrar:
                on_cerrar()

        super().__init__(
            modal=True,
            bgcolor=Colores.BLANCO,
            title=ft.Row([
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=Colores.ROJO, size=22),
                ft.Text(
                    "Conflicto de horario",
                    font_family=Fuentes.TITULO,
                    size=17,
                    color=Colores.ROJO,
                ),
            ], spacing=8),
            content=ft.Container(
                content=ft.Column(detalles, spacing=4),
                width=420,
                padding=ft.padding.symmetric(vertical=4),
            ),
            actions=[
                ft.ElevatedButton(
                    "Entendido",
                    on_click=_cerrar,
                    bgcolor=Colores.AZUL_PRIMARIO,
                    color=Colores.BLANCO,
                    elevation=0,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.padding.symmetric(horizontal=24, vertical=10),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
