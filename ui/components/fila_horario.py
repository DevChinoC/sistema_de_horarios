"""
Componente FilaHorario.

Fila de un mini-formulario de horario: Día | Hora inicio | Hora fin | [×].
Extraído de detalle_plan_view.py — P1 componentización.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes
from ui.components.time_picker import ScrollTimePicker

_BLANCO = "#F8F3F3"
_DIAS  = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# ── Constantes de layout (copiadas de la view original) ───────
_W_DIA  = 130
_W_HORA = 164

# ── Helpers de estilo ─────────────────────────────────────────

def _dd_kw(width: int) -> dict:
    return dict(
        width=width,

        bgcolor=Colores.BLANCO,
        fill_color=Colores.BLANCO,
        color= "#000000",

        text_style=ft.TextStyle(
            color= "#000000",
            font_family=Fuentes.CAMPOS,
            size=13
        ),

        hint_style=ft.TextStyle(
            color=Colores.TEXTO_MUTED,
            font_family=Fuentes.CAMPOS,
            size=13
        ),

        border_color=Colores.BORDE,
        focused_border_color=Colores.AZUL_PRIMARIO,

        content_padding=ft.padding.symmetric(
            horizontal=10,
            vertical=6
        ),

        dense=True,
    )
def _opcion(key: str, text: str) -> ft.dropdown.Option:
    return ft.dropdown.Option(
        key=key, text=text,
        text_style=ft.TextStyle(color= "#000000", font_family=Fuentes.CAMPOS),
    )


class FilaHorario(ft.Row):
    """Fila de formulario de horario con día, hora inicio, hora fin y botón quitar.

    Uso:
        fila = FilaHorario(on_quitar=..., on_change=...)
        dia = fila.dd_dia.value          # "Lunes", "Martes"…
        ini = fila.hora_inicio.get_24h() # "07:00"
        fin = fila.hora_fin.get_24h()    # "09:00"
    """

    def __init__(self, on_quitar: Callable, on_change: Callable) -> None:
        self.dd_dia = ft.Dropdown(
            hint_text="Seleccionar dia",
            options=[_opcion(d, d) for d in _DIAS],
            menu_height=150,
            **_dd_kw(_W_DIA),
        )
        self.hora_inicio = ScrollTimePicker(on_change=on_change)
        self.hora_fin    = ScrollTimePicker(on_change=on_change)
        btn_quitar = ft.IconButton(
            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
            icon_color=Colores.ROJO, icon_size=18,
            on_click=lambda _: on_quitar(self),
            tooltip="Quitar fila",
        )
        super().__init__(
            controls=[self.dd_dia, self.hora_inicio, self.hora_fin, btn_quitar],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def to_raw(self) -> dict:
        """Exporta los valores de la fila como dict para mappers."""
        return {
            "dia":         self.dd_dia.value or "",
            "hora_inicio": self.hora_inicio.get_24h(),
            "hora_fin":    self.hora_fin.get_24h(),
        }
