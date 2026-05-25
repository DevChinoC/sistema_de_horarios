"""
Widgets de entrada de tiempo (scroll picker de hora).

Extraído de detalle_plan_view.py — P1 Fase de componentización.

Contiene:
- _ScrollColumn: columna con botones ▲/▼, rueda del mouse, touchpad y teclado
- ScrollTimePicker: picker HH:MM A.M/P.M compuesto de ScrollColumns
"""
from __future__ import annotations

from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes

_NEGRO = "#000000"


class ScrollColumn(ft.Container):
    """Columna de valor con botones ▲/▼, scroll del mouse,
    arrastre vertical (touchpad) y teclas ↑/↓ del teclado.

    Al hacer clic se enfoca el control (borde azul); las flechas
    del teclado cambian el valor. Solo una instancia puede estar
    enfocada a la vez.
    """

    _focused_instance: "ScrollColumn | None" = None

    def __init__(
        self,
        items: list[str],
        initial: int = 0,
        width: int = 36,
        on_change: Callable | None = None,
    ) -> None:
        self._items      = items
        self._selected   = initial
        self._on_change  = on_change
        self._drag_accum = 0.0

        self._txt = ft.Text(
            items[initial], size=14, weight=ft.FontWeight.W_700,
            color=_NEGRO, font_family=Fuentes.CAMPOS,
            text_align=ft.TextAlign.CENTER,
        )
        self._box = ft.Container(
            content=self._txt,
            width=width, height=30,
            alignment=ft.alignment.center,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=4,
            bgcolor=Colores.BLANCO,
        )

        btn_up = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_DROP_UP,
                            size=18, color=Colores.TEXTO_MUTED),
            on_click=lambda _: self._move(-1),
            width=width, height=16,
            alignment=ft.alignment.center,
            ink=True,
        )
        btn_down = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN,
                            size=18, color=Colores.TEXTO_MUTED),
            on_click=lambda _: self._move(1),
            width=width, height=16,
            alignment=ft.alignment.center,
            ink=True,
        )
        self._gesture = ft.GestureDetector(
            content=self._box,
            on_scroll=self._on_scroll,
            on_tap=self._on_tap,
            on_vertical_drag_update=self._on_drag,
        )
        inner = ft.Column(
            controls=[btn_up, self._gesture, btn_down],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        super().__init__(content=inner, width=width, height=62)

    # ── Ciclo de vida ──────────────────────────────────────────

    def did_mount(self) -> None:
        if self.page:
            self.page.on_keyboard_event = ScrollColumn._global_on_key

    def will_unmount(self) -> None:
        if ScrollColumn._focused_instance is self:
            ScrollColumn._focused_instance = None

    # ── Interacción ────────────────────────────────────────────

    def _on_scroll(self, e: ft.ScrollEvent) -> None:
        self._move(-1 if e.scroll_delta_y < 0 else 1)

    def _on_drag(self, e) -> None:
        self._drag_accum += e.delta_y
        if abs(self._drag_accum) >= 20:
            self._move(1 if self._drag_accum > 0 else -1)
            self._drag_accum = 0.0

    def _on_tap(self, _) -> None:
        prev = ScrollColumn._focused_instance
        if prev is not None and prev is not self:
            prev._lose_focus()
        ScrollColumn._focused_instance = self
        self._box.border = ft.border.all(2, Colores.AZUL_PRIMARIO)
        if self.page:
            self._box.update()

    def _lose_focus(self) -> None:
        self._box.border = ft.border.all(1, Colores.BORDE)
        if self.page:
            self._box.update()

    @staticmethod
    def _global_on_key(e: ft.KeyboardEvent) -> None:
        inst = ScrollColumn._focused_instance
        if inst is None:
            return
        if e.key == "Arrow Up":
            inst._move(-1)
        elif e.key == "Arrow Down":
            inst._move(1)

    def _move(self, direction: int) -> None:
        self._select((self._selected + direction) % len(self._items))

    def _select(self, idx: int) -> None:
        self._selected = idx
        self._txt.value = self._items[idx]
        if self.page:
            self._txt.update()
        if self._on_change:
            self._on_change(self._items[idx])

    @property
    def value(self) -> str:
        return self._items[self._selected]

    @value.setter
    def value(self, v: str) -> None:
        if v in self._items:
            self._select(self._items.index(v))


class ScrollTimePicker(ft.Row):
    """Picker HH:MM A.M/P.M controlado con rueda del mouse."""

    _HOURS = [f"{h}" for h in range(1, 13)]
    _MINS  = [f"{m:02d}" for m in range(0, 60)]
    _AMPM  = ["A.M", "P.M"]

    def __init__(self, on_change: Callable | None = None) -> None:
        self._on_change = on_change
        self._h  = ScrollColumn(self._HOURS, 0, 34, lambda _: self._notify())
        self._m  = ScrollColumn(self._MINS,  0, 34, lambda _: self._notify())
        self._ap = ScrollColumn(self._AMPM,  0, 42, lambda _: self._notify())
        super().__init__(
            controls=[
                self._h,
                ft.Text(":", size=15, weight=ft.FontWeight.BOLD,
                        color=_NEGRO, font_family=Fuentes.CAMPOS),
                self._m,
                ft.Container(width=4),
                self._ap,
            ],
            spacing=2,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _notify(self) -> None:
        if self._on_change:
            self._on_change(None)

    def get_24h(self) -> str:
        h, m = int(self._h.value), int(self._m.value)
        if self._ap.value == "A.M":
            h = 0 if h == 12 else h
        else:
            h = h if h == 12 else h + 12
        return f"{h:02d}:{m:02d}"

    def set_from_24h(self, valor_24h: str) -> None:
        try:
            h24, m = int(valor_24h.split(":")[0]), int(valor_24h.split(":")[1])
            if h24 == 0:      h12, ap = 12, "A.M"
            elif h24 < 12:    h12, ap = h24, "A.M"
            elif h24 == 12:   h12, ap = 12, "P.M"
            else:             h12, ap = h24 - 12, "P.M"
            self._h.value  = str(h12)
            self._m.value  = f"{m:02d}"
            self._ap.value = ap
        except (ValueError, IndexError):
            pass

    @property
    def value(self) -> str:
        return self.get_24h()
