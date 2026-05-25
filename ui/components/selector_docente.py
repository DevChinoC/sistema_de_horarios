"""
Componente UI: SelectorDocente

Dropdown de docente con opción '+ Otro' para crear nuevo.
Extraído de DetallePlanView (_DropdownConNuevo para docentes).

SOLO UI: no contiene lógica de negocio.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes
from ui.utils.reset_utils import reset_dropdown

_NEGRO    = "#000000"
_KEY_NUEVO = "__nuevo__"


def _opcion(key: str, text: str) -> ft.dropdown.Option:
    return ft.dropdown.Option(
        key=key, text=text,
        text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS),
    )


def _opcion_nuevo() -> ft.dropdown.Option:
    return ft.dropdown.Option(
        key=_KEY_NUEVO,
        content=ft.Container(
            content=ft.Text(
                "+ Otro", color=Colores.BLANCO, size=13,
                weight=ft.FontWeight.W_600, font_family=Fuentes.CAMPOS,
            ),
            bgcolor=Colores.AZUL_PRIMARIO,
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            expand=True,
        ),
    )


class SelectorDocente(ft.Stack):
    """Dropdown de docente que al elegir '+ Otro' muestra un TextField.

    Al presionar Enter en el TextField, invoca on_crear(nombre) para
    que el controller cree el docente en BD y actualice las opciones.

    Uso:
        sel = SelectorDocente(
            docentes=lista_de_DocenteDTO,
            on_crear=lambda nombre: controller.crear_docente(nombre),
            width=220,
        )
    """

    def __init__(
        self,
        docentes: list,
        width: int,
        on_crear: Callable[[str], None] | None = None,
    ) -> None:
        self._on_crear = on_crear
        self._width = width

        opts = [_opcion(str(d.id), d.nombre) for d in docentes] + [_opcion_nuevo()]

        self._dd = ft.Dropdown(
            hint_text="Seleccionar docente",
            options=opts,
            on_change=self._on_dd_change,
            menu_height=150,
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            bgcolor=Colores.BLANCO,
            fill_color=Colores.BLANCO,
            color=_NEGRO,
            text_size=13,
            width=width,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS),
            hint_style=ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
        )
        self._tf = ft.TextField(
            visible=False,
            on_submit=self._on_tf_submit,
            on_blur=self._on_tf_blur,
            hint_text="Escriba y presione Enter…",
            width=width,
            text_size=13,
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            bgcolor=Colores.BLANCO,
            color=_NEGRO,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
            text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS),
            hint_style=ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
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
        self, docentes: list, seleccion: str | None = None,
    ) -> None:
        opts = [_opcion(str(d.id), d.nombre) for d in docentes] + [_opcion_nuevo()]
        self._dd.options = opts
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

    def reset(self, docentes: list | None = None) -> None:
        opts = (
            [_opcion(str(d.id), d.nombre) for d in docentes] + [_opcion_nuevo()]
            if docentes is not None else self._dd.options
        )
        self._dd = reset_dropdown(self._dd, options=opts, disabled=False)
        self._dd.on_change = self._on_dd_change
        self._tf.visible = False
        if self.page:
            self._tf.update()

    # ── Callbacks ────────────────────────────────────────────

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
