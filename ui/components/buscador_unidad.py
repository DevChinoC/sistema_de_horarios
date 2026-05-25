"""
Componente BuscadorUnidad.

Campo de búsqueda con lista scrollable de unidades de aprendizaje.
Al escribir, filtra las opciones cargadas y muestra resultados debajo
del TextField. Al hacer clic en un resultado se invoca on_seleccionar(key, text).

Extraído de detalle_plan_view.py — P1 componentización.
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes

_NEGRO = "#000000"


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


class BuscadorUnidad(ft.Column):
    """Campo de búsqueda con lista scrollable de coincidencias.

    Uso:
        buscador = BuscadorUnidad(
            width=300,
            on_seleccionar=lambda key, text: ...,
            on_cerrar=lambda _: ...,
        )
        buscador.set_opciones([(key, text), ...])
        buscador.activar()    # muestra y enfoca
        buscador.desactivar() # oculta
    """

    _MAX_RESULTADOS_VISIBLES = 150

    def __init__(
        self,
        width: int,
        on_seleccionar: Callable[[str, str], None],
        on_cerrar: Callable,
    ) -> None:
        self._on_seleccionar = on_seleccionar
        self._on_cerrar      = on_cerrar
        self._opciones: list[tuple[str, str]] = []

        self._tf = ft.TextField(
            on_change=self._filtrar,
            prefix=ft.Icon(ft.Icons.SEARCH, color=Colores.AZUL_PRIMARIO, size=18),
            suffix=ft.Container(
                content=ft.Icon(ft.Icons.CLOSE, color=Colores.ROJO, size=18),
                on_click=lambda _: self._on_cerrar(_),
                tooltip="Cerrar búsqueda",
                ink=True,
                padding=ft.padding.all(2),
            ),
            **_tf_kw(width, hint="Escriba para filtrar…"),
        )
        self._lista = ft.ListView(spacing=0, height=self._MAX_RESULTADOS_VISIBLES)
        self._contenedor_lista = ft.Container(
            content=self._lista,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=ft.border_radius.only(bottom_left=6, bottom_right=6),
            bgcolor=Colores.BLANCO,
            width=width,
            visible=False,
        )
        super().__init__(
            controls=[self._tf, self._contenedor_lista],
            spacing=0,
            width=width,
            visible=False,
        )

    # ── API pública ───────────────────────────────────────────

    def set_opciones(self, opciones: list[tuple[str, str]]) -> None:
        """Establece las opciones disponibles para filtrar."""
        self._opciones = opciones

    def activar(self) -> None:
        """Muestra el buscador, limpia el campo y enfoca."""
        self.visible = True
        self._tf.value = ""
        self._lista.controls = []
        self._contenedor_lista.visible = False
        if self.page:
            self.update()
            self._tf.focus()

    def desactivar(self) -> None:
        """Oculta el buscador y limpia resultados."""
        self.visible = False
        self._tf.value = ""
        self._lista.controls = []
        self._contenedor_lista.visible = False
        if self.page:
            self.update()

    def set_width(self, width: int) -> None:
        """Actualiza el ancho del buscador y sus controles internos."""
        self.width = width
        self._tf.width = width
        self._contenedor_lista.width = width

    # ── Filtrado interno ──────────────────────────────────────

    def _filtrar(self, _) -> None:
        texto = (self._tf.value or "").strip().lower()
        if not texto:
            self._lista.controls = []
            self._contenedor_lista.visible = False
        else:
            coincidencias = [(k, t) for k, t in self._opciones if texto in t.lower()]
            self._lista.controls = [self._crear_item(k, t) for k, t in coincidencias]
            self._contenedor_lista.visible = bool(coincidencias)
        if self.page:
            self._lista.update()
            self._contenedor_lista.update()

    def _crear_item(self, key: str, text: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(text, size=13, color=_NEGRO, font_family=Fuentes.CAMPOS),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=lambda _, k=key, t=text: self._seleccionar(k, t),
            ink=True,
            on_hover=self._hover_item,
            border=ft.border.only(bottom=ft.BorderSide(0.5, Colores.BORDE)),
        )

    def _hover_item(self, e) -> None:
        e.control.bgcolor = (
            ft.Colors.with_opacity(0.08, Colores.AZUL_PRIMARIO)
            if e.data == "true" else None
        )
        if self.page:
            e.control.update()

    def _seleccionar(self, key: str, text: str) -> None:
        self._on_seleccionar(key, text)
