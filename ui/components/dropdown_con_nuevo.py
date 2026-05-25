"""
Componente DropdownConNuevo.

Dropdown que al elegir '+ Otro' se convierte en TextField para crear
un nuevo registro en BD. Al presionar Enter se crea y el Dropdown
se restaura con el nuevo elemento seleccionado.

Extraído de detalle_plan_view.py — P1 componentización.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes
from ui.utils.reset_utils import reset_dropdown

_NEGRO    = "#FFFFFF"
_KEY_NUEVO = "__nuevo__"


def _dd_kw(width: int) -> dict:
    return dict(
        width=width,
        text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS, size=13),
        hint_style=ft.TextStyle(color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS, size=13),
        border_color=Colores.BORDE,
        focused_border_color=Colores.AZUL_PRIMARIO,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        dense=True,
    )
def _dd_kw(width: int) -> dict:
    return dict(
        width=width,

        bgcolor=Colores.BLANCO,
        fill_color=Colores.BLANCO,
        color=_NEGRO,

        text_style=ft.TextStyle(
            color=_NEGRO,
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

def _tf_kw(width: int, hint: str = "") -> dict:
    return dict(
        width=width,
        text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS, size=13),
        hint_text=hint,
        hint_style=ft.TextStyle(color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS, size=13),
        border_color=Colores.BORDE,
        focused_border_color=Colores.AZUL_PRIMARIO,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        dense=True,
    )


class DropdownConNuevo(ft.Stack):
    """Dropdown con opción '+ Otro' que abre un TextField inline.

    Uso:
        dd = DropdownConNuevo(
            hint_text="Seleccionar aula",
            opciones_iniciales=[...],
            width=200,
            on_crear=lambda nombre: crear_aula(nombre),
        )
        dd.value         # key seleccionado o None
        dd.value = "5"   # establece selección
        dd.reconstruir_opciones([...], seleccion="5")
        dd.reset()       # limpia visualmente
    """

    def __init__(
        self,
        hint_text: str,
        opciones_iniciales: list[ft.dropdown.Option],
        width: int,
        on_crear: Callable[[str], None] | None = None,
    ) -> None:
        self._on_crear = on_crear

        self._dd = ft.Dropdown(
            hint_text=hint_text,
            options=opciones_iniciales,
            on_change=self._on_dd_change,
            menu_height=150,
            **_dd_kw(width),
        )
        self._tf = ft.TextField(
            visible=False,
            on_submit=self._on_tf_submit,
            on_blur=self._on_tf_blur,
            **_tf_kw(width, hint="Escriba y presione Enter…"),
        )
        super().__init__(controls=[self._dd, self._tf], width=width)

    # ── API pública ───────────────────────────────────────────

    @property
    def value(self) -> str | None:
        return self._dd.value

    @value.setter
    def value(self, v: str | None) -> None:
        self._dd.value = v
        if self.page:
            self._dd.update()

    def reconstruir_opciones(
        self,
        nuevas: list[ft.dropdown.Option],
        seleccion: str | None = None,
    ) -> None:
        self._dd.options = nuevas
        self._dd.value   = seleccion
        if self.page:
            self._dd.update()

    def restaurar_dd(self, seleccion: str | None) -> None:
        self._dd.value   = seleccion
        self._dd.visible = True
        self._tf.visible = False
        if self.page:
            self._dd.update()
            self._tf.update()

    def reset(self, opciones: list[ft.dropdown.Option] | None = None) -> None:
        """Destruye y recrea el Dropdown interno para forzar limpieza visual."""
        self._dd = reset_dropdown(
            self._dd,
            options=opciones if opciones is not None else self._dd.options,
            disabled=False,
        )
        self._dd.on_change = self._on_dd_change
        self._tf.visible = False
        if self.page:
            self._tf.update()

    # ── Callbacks internos ────────────────────────────────────

    def _on_dd_change(self, _) -> None:
        if self._dd.value == _KEY_NUEVO:
            self._dd.visible = False
            self._tf.visible = True
            self._tf.value   = ""
            if self.page:
                self._dd.update()
                self._tf.update()
                self._tf.focus()

    def _on_tf_submit(self, _) -> None:
        nombre = (self._tf.value or "").strip()
        if not nombre:
            self.restaurar_dd(None)
            return
        if self._on_crear:
            self._on_crear(nombre)

    def _on_tf_blur(self, _) -> None:
        if self._tf.visible and not (self._tf.value or "").strip():
            self.restaurar_dd(None)
