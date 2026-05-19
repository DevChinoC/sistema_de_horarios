import flet as ft
import os
import tempfile
from functools import partial
from typing import Callable
from datetime import datetime

from application.services.horario_service import HorarioService
from application.dto.horario_dto import GuardarHorarioDTO, FilaHorarioDTO
from ui.components.plan_components import Colores, Fuentes, DialogoConfirmacion
from ui.pdf.generador_pdf import GeneradorPDF
from ui.views.horario_state import HorarioStateManager
from ui.utils.reset_utils import reset_dropdown

# ─────────────────────────────────────────────────────────────
# Constantes de layout
# ─────────────────────────────────────────────────────────────
_PAD_H         = 30
_W_SEM         = 220
_W_UA          = 220
_W_AULA        = 220
_W_DOC         = 220
_W_PER         = 220
_W_DIA         = 120
_W_HORA        = 125   # ancho picker HH:MM AM/PM
_COLOR_HDR     = "#3D5FD2"  # azul oscuro para header/footer de horario
_KEY_NUEVO     = "__nuevo__"

_NEGRO         = "#000000"   # negro sólido para texto de opciones y valores


# ─────────────────────────────────────────────────────────────
# Helpers puros de estilo
# ─────────────────────────────────────────────────────────────

def _opcion(key: str, text: str) -> ft.dropdown.Option:
    """Opción con texto negro sólido."""
    return ft.dropdown.Option(
        key=key, text=text,
        text_style=ft.TextStyle(
            color=_NEGRO,
            font_family=Fuentes.CAMPOS,
        ),
    )


def _opcion_nuevo() -> ft.dropdown.Option:
    """Opción especial '+ Otro' con relleno azul y letras blancas."""
    return ft.dropdown.Option(
        key=_KEY_NUEVO,
        content=ft.Container(
            content=ft.Text(
                "+ Otro",
                color=Colores.BLANCO,
                size=13,
                weight=ft.FontWeight.W_600,
                font_family=Fuentes.CAMPOS,
            ),
            bgcolor=Colores.AZUL_PRIMARIO,
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            expand=True,
        ),
    )


def _dd_kw(width: int) -> dict:
    """kwargs comunes para ft.Dropdown — valor y opciones siempre negro."""
    return dict(
        border_color=Colores.BORDE,
        focused_border_color=Colores.AZUL_PRIMARIO,
        bgcolor=Colores.BLANCO,
        fill_color=Colores.BLANCO,         
        color=_NEGRO,                      
        text_size=13,
        width=width,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_style=ft.TextStyle(
            color=_NEGRO,                  
            font_family=Fuentes.CAMPOS,
        ),
        hint_style=ft.TextStyle(
            color=Colores.TEXTO_MUTED,
            font_family=Fuentes.CAMPOS,
        ),
    )


def _tf_kw(width: int, hint: str = "") -> dict:
    """kwargs comunes para ft.TextField."""
    return dict(
        hint_text=hint,
        width=width,
        text_size=13,
        border_color=Colores.BORDE,
        focused_border_color=Colores.AZUL_PRIMARIO,
        bgcolor=Colores.BLANCO,
        color=_NEGRO,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_style=ft.TextStyle(
            color=_NEGRO, font_family=Fuentes.CAMPOS),
        hint_style=ft.TextStyle(
            color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
    )


def _lbl(texto: str) -> ft.Text:
    return ft.Text(
        texto, size=13, weight=ft.FontWeight.W_600,
        color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
    )


# ─────────────────────────────────────────────────────────────
# Cabecera
# ─────────────────────────────────────────────────────────────
class _Cabecera(ft.Container):
    def __init__(self, on_cerrar: Callable) -> None:
        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_MONTH,
                            color=Colores.AZUL_PRIMARIO, size=36),
                    ft.Text(
                        "Gestión de planes y horarios",
                        size=24, weight=ft.FontWeight.W_400,
                        color=Colores.AZUL_PRIMARIO,
                        font_family=Fuentes.TITULO,
                        text_align=ft.TextAlign.CENTER,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=Colores.BLANCO,
                        bgcolor=Colores.ROJO,
                        icon_size=18,
                        on_click=on_cerrar,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=0),
                            padding=ft.padding.all(8),
                        ),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colores.BLANCO,
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border=ft.border.only(
                bottom=ft.BorderSide(3, Colores.AZUL_PRIMARIO)),
        )


# ─────────────────────────────────────────────────────────────
# Picker de hora con scroll, touchpad, teclado (↑ / ↓) y botones
# ─────────────────────────────────────────────────────────────
class _ScrollColumn(ft.Container):
    """Columna de valor con botones ▲/▼, scroll del mouse,
    arrastre vertical (touchpad) y teclas ↑ / ↓ del teclado.

    Al hacer clic se enfoca el control (borde azul); las flechas
    del teclado cambian el valor.  Solo una instancia puede estar
    enfocada a la vez.

    Se usa ft.Container como base (no ft.Column) para evitar
    problemas de layout cuando se inserta dentro de ft.Row.
    """

    _focused_instance: "_ScrollColumn | None" = None  # instancia enfocada

    def __init__(
        self,
        items: list[str],
        initial: int = 0,
        width: int = 36,
        on_change: Callable | None = None,
    ) -> None:
        self._items     = items
        self._selected  = initial
        self._on_change = on_change
        self._drag_accum = 0.0  # acumulador para touchpad

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

        # Botón ▲
        btn_up = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_DROP_UP,
                            size=18, color=Colores.TEXTO_MUTED),
            on_click=lambda _: self._move(-1),
            width=width, height=16,
            alignment=ft.alignment.center,
            ink=True,
        )
        # Botón ▼
        btn_down = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_DROP_DOWN,
                            size=18, color=Colores.TEXTO_MUTED),
            on_click=lambda _: self._move(1),
            width=width, height=16,
            alignment=ft.alignment.center,
            ink=True,
        )

        # GestureDetector envuelve la caja para scroll + touchpad + clic
        self._gesture = ft.GestureDetector(
            content=self._box,
            on_scroll=self._on_scroll,
            on_tap=self._on_tap,
            on_vertical_drag_update=self._on_drag,
        )

        # Columna interna con altura fija para evitar layout unbounded
        inner = ft.Column(
            controls=[btn_up, self._gesture, btn_down],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=inner,
            width=width,
            height=62,  # 16 + 30 + 16
        )

    # ── Ciclo de vida ──────────────────────────────────────

    def did_mount(self) -> None:
        """Registrar handler de teclado global (siempre re-registra)."""
        if self.page:
            self.page.on_keyboard_event = _ScrollColumn._global_on_key

    def will_unmount(self) -> None:
        """Limpiar referencia si esta instancia estaba enfocada."""
        if _ScrollColumn._focused_instance is self:
            _ScrollColumn._focused_instance = None

    # ── Interacción: scroll (rueda del mouse) ──────────────

    def _on_scroll(self, e: ft.ScrollEvent) -> None:
        self._move(-1 if e.scroll_delta_y < 0 else 1)

    # ── Interacción: arrastre vertical (touchpad) ──────────

    def _on_drag(self, e) -> None:
        self._drag_accum += e.delta_y
        threshold = 20  # píxeles antes de cambiar valor
        if abs(self._drag_accum) >= threshold:
            direction = 1 if self._drag_accum > 0 else -1
            self._move(direction)
            self._drag_accum = 0.0

    # ── Interacción: clic para enfocar ─────────────────────

    def _on_tap(self, _) -> None:
        prev = _ScrollColumn._focused_instance
        if prev is not None and prev is not self:
            prev._lose_focus()
        _ScrollColumn._focused_instance = self
        self._box.border = ft.border.all(2, Colores.AZUL_PRIMARIO)
        if self.page:
            self._box.update()

    def _lose_focus(self) -> None:
        self._box.border = ft.border.all(1, Colores.BORDE)
        if self.page:
            self._box.update()

    # ── Interacción: teclado (↑ / ↓) ──────────────────────

    @staticmethod
    def _global_on_key(e: ft.KeyboardEvent) -> None:
        inst = _ScrollColumn._focused_instance
        if inst is None:
            return
        if e.key == "Arrow Up":
            inst._move(-1)
        elif e.key == "Arrow Down":
            inst._move(1)

    # ── Lógica compartida ─────────────────────────────────

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


class _ScrollTimePicker(ft.Row):
    """Picker HH : MM  A.M/P.M controlado con rueda del mouse."""

    _HOURS = [f"{h}" for h in range(1, 13)]
    _MINS  = [f"{m:02d}" for m in range(0, 60)]
    _AMPM  = ["A.M", "P.M"]

    def __init__(self, on_change: Callable | None = None) -> None:
        self._on_change = on_change
        self._h  = _ScrollColumn(self._HOURS, 0, 34, lambda _: self._notify())
        self._m  = _ScrollColumn(self._MINS,  0, 34, lambda _: self._notify())
        self._ap = _ScrollColumn(self._AMPM,  0, 42, lambda _: self._notify())

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
        """Establece el picker a partir de un valor HH:MM en formato 24h."""
        try:
            parts = valor_24h.split(":")
            h24, m = int(parts[0]), int(parts[1])
            if h24 == 0:
                h12, ap = 12, "A.M"
            elif h24 < 12:
                h12, ap = h24, "A.M"
            elif h24 == 12:
                h12, ap = 12, "P.M"
            else:
                h12, ap = h24 - 12, "P.M"
            self._h.value  = str(h12)
            self._m.value  = f"{m:02d}"
            self._ap.value = ap
        except (ValueError, IndexError):
            pass

    @property
    def value(self) -> str:
        return self.get_24h()


# ─────────────────────────────────────────────────────────────
# Fila de horario: Día | Hora inicio | Hora fin | [×]
# ─────────────────────────────────────────────────────────────
class _FilaHorario(ft.Row):
    _DIAS = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    def __init__(self, on_quitar: Callable, on_change: Callable) -> None:
        self.dd_dia = ft.Dropdown(
            hint_text="Seleccionar dia",
            options=[_opcion(d, d) for d in self._DIAS],
            menu_height=150,
            **_dd_kw(_W_DIA),
        )
        self.hora_inicio = _ScrollTimePicker(on_change=on_change)
        self.hora_fin    = _ScrollTimePicker(on_change=on_change)
        btn_quitar = ft.IconButton(
            icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
            icon_color=Colores.ROJO, icon_size=18,
            on_click=lambda _: on_quitar(self),
            tooltip="Quitar fila",
        )
        super().__init__(
            controls=[self.dd_dia, self.hora_inicio,
                       self.hora_fin, btn_quitar],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )


# ─────────────────────────────────────────────────────────────
# Dropdown que se convierte en TextField al elegir "+ Otro"
# ─────────────────────────────────────────────────────────────
class _DropdownConNuevo(ft.Stack):
    """Al elegir '+ Otro' (opción con relleno azul dentro del
    desplegable), el Dropdown se oculta y aparece un TextField
    editable.  Al presionar Enter se crea en BD y se restaura
    el Dropdown con el nuevo elemento seleccionado."""

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
        """Destruye y recrea el Dropdown interno para forzar limpieza visual.

        Usa ``reset_dropdown`` para evitar el bug de Flet donde
        ``dropdown.value = None`` no limpia el texto renderizado.
        """
        self._dd = reset_dropdown(
            self._dd,
            options=opciones if opciones is not None else self._dd.options,
            disabled=False,
        )
        # Reasignar on_change ya que reset_dropdown lo copia del viejo
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


# ─────────────────────────────────────────────────────────────
# Buscador de unidad de aprendizaje con lista de resultados
# ─────────────────────────────────────────────────────────────
class _BuscadorUnidad(ft.Column):
    """Campo de búsqueda con lista scrollable de coincidencias.

    Al escribir, filtra las opciones cargadas y muestra los
    resultados debajo del TextField en un ListView con scroll.
    Al hacer clic en un resultado se invoca on_seleccionar(key, text).
    """

    _MAX_RESULTADOS_VISIBLES = 150   # altura máxima de la lista (px)

    def __init__(
        self,
        width: int,
        on_seleccionar: Callable[[str, str], None],
        on_cerrar: Callable,
    ) -> None:
        self._on_seleccionar = on_seleccionar
        self._on_cerrar = on_cerrar
        self._opciones: list[tuple[str, str]] = []  # (key, text)

        self._tf = ft.TextField(
            on_change=self._filtrar,
            prefix=ft.Icon(ft.Icons.SEARCH,
                           color=Colores.AZUL_PRIMARIO, size=18),
            suffix=ft.Container(
                content=ft.Icon(ft.Icons.CLOSE,
                                color=Colores.ROJO, size=18),
                on_click=lambda _: self._on_cerrar(_),
                tooltip="Cerrar búsqueda",
                ink=True,
                padding=ft.padding.all(2),
            ),
            **_tf_kw(width, hint="Escriba para filtrar…"),
        )

        self._lista = ft.ListView(
            spacing=0,
            height=self._MAX_RESULTADOS_VISIBLES,
            padding=ft.padding.all(0),
        )

        self._contenedor_lista = ft.Container(
            content=self._lista,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=ft.border_radius.only(
                bottom_left=6, bottom_right=6),
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
        """Filtra las opciones según lo escrito y actualiza la lista."""
        texto = (self._tf.value or "").strip().lower()
        if not texto:
            self._lista.controls = []
            self._contenedor_lista.visible = False
        else:
            coincidencias = [
                (key, text) for key, text in self._opciones
                if texto in text.lower()
            ]
            self._lista.controls = [
                self._crear_item(key, text)
                for key, text in coincidencias
            ]
            self._contenedor_lista.visible = len(coincidencias) > 0
        if self.page:
            self._lista.update()
            self._contenedor_lista.update()

    def _crear_item(self, key: str, text: str) -> ft.Container:
        """Crea un ítem clickable para la lista de resultados."""
        return ft.Container(
            content=ft.Text(
                text, size=13, color=_NEGRO,
                font_family=Fuentes.CAMPOS,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            on_click=lambda _, k=key, t=text: self._seleccionar(k, t),
            ink=True,
            on_hover=self._hover_item,
            border=ft.border.only(
                bottom=ft.BorderSide(0.5, Colores.BORDE)),
        )

    def _hover_item(self, e) -> None:
        """Resalta el ítem al pasar el cursor."""
        e.control.bgcolor = (
            ft.Colors.with_opacity(0.08, Colores.AZUL_PRIMARIO)
            if e.data == "true" else None
        )
        if self.page:
            e.control.update()

    def _seleccionar(self, key: str, text: str) -> None:
        """Invoca el callback de selección con la opción elegida."""
        self._on_seleccionar(key, text)


# ─────────────────────────────────────────────────────────────
# Vista principal de detalle de plan
# ─────────────────────────────────────────────────────────────
class DetallePlanView(ft.Column):
    """Vista de detalle del plan con formulario de asignación de horario.

    Layout (3 columnas, sin caja contenedora del formulario):
    Col1 : Semestre + mini-tabla Horario
    Col2 : Unidad de aprendizaje + Aulas + Periodo
    Col3 : Tipo (solo lectura) + Docente + botón Agregar
    """

    def __init__(
        self,
        page: ft.Page,
        id_plan: int,
        service: HorarioService,
        on_volver: Callable,
        ruta_membrete: str | None = None,
        id_plan_generado: int | None = None,
    ) -> None:
        self._page          = page
        self._id_plan       = id_plan
        self._service       = service
        self._on_volver     = on_volver
        # Cargar membrete desde la BD (prioritario) o parámetro de respaldo
        self._ruta_membrete = service.obtener_ruta_membrete(id_plan) or ruta_membrete
        # ID del plan generado para precargar horarios desde historial
        self._id_plan_generado_precarga = id_plan_generado

        # ── FilePicker para guardar PDF ────────────────────────
        self._save_picker = ft.FilePicker(on_result=self._on_save_result)

        # ── Datos iniciales ───────────────────────────────────
        nombre_plan     = service.obtener_nombre_plan(id_plan)
        semestres_raw   = service.obtener_semestres(id_plan)
        self._sem_opt   = next((s for s in semestres_raw if s.numero == 0), None)
        self._semestres = [s for s in semestres_raw if s.numero > 0]
        # LIES tabs solo visibles para MIIDT
        self._all_lies  = service.obtener_lies_del_plan(id_plan)
        self._aulas     = list(service.obtener_aulas())
        self._docentes  = list(service.obtener_docentes())
        self._tipos     = service.obtener_tipos_materia()
        self._unidades  = []

        if self._all_lies:
            _id_lies_init = self._all_lies[0].id
        else:
            _all = service.obtener_todas_lies_del_plan(id_plan)
            _id_lies_init = _all[0].id if _all else 0
        self._id_lies_activa = _id_lies_init

        # ── Estado centralizado (sesión, cachés, validación) ──
        self._state = HorarioStateManager(
            service=service,
            id_plan=id_plan,
            id_lies_activa=_id_lies_init,
            sem_opt_id=self._sem_opt.id if self._sem_opt else None,
        )

        # ════════════════════ LIES TABS ═══════════════════════
        self._lies_btns: list[ft.OutlinedButton] = []
        for lies in self._all_lies:
            activo = lies.id == self._id_lies_activa
            btn = ft.OutlinedButton(
                text=lies.nombre,
                on_click=lambda _, lid=lies.id, ln=lies.nombre:
                    self._on_lies_cambiado(lid, ln),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=5),
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    bgcolor=Colores.AZUL_PRIMARIO if activo else "transparent",
                    color=Colores.BLANCO if activo else Colores.AZUL_PRIMARIO,
                    side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                    text_style=ft.TextStyle(
                        font_family=Fuentes.TITULO, size=14),
                ),
            )
            self._lies_btns.append(btn)

        lies_row = ft.Row(
            controls=[_lbl("Lies:"), *self._lies_btns],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ) if self._all_lies else ft.Container()

        # ════════════════════ COL 1 ════════════════════════════
        self._dd_semestre = ft.Dropdown(
            hint_text="Seleccionar semestre",
            options=[_opcion(str(s.id), f"Semestre {s.numero}")
                     for s in self._semestres],
            on_change=self._on_semestre_cambiado,
            menu_height=150,
            **_dd_kw(_W_SEM),
        )

        # Filas de horario
        self._filas_horario: list[_FilaHorario] = []
        self._col_horarios = ft.Column(controls=[], spacing=4)
        fila0 = _FilaHorario(
            on_quitar=self._quitar_fila,
            on_change=self._actualizar_total,
        )
        self._filas_horario.append(fila0)
        self._col_horarios.controls.append(fila0)

        self._lbl_total = ft.Text(
            "0 Horas", color=Colores.BLANCO, size=13,
            font_family=Fuentes.CAMPOS, weight=ft.FontWeight.W_600,
        )

        # Ancho de la mini-tabla de horario
        w_hor = _W_DIA + _W_HORA * 2 + 60

        horario_header = ft.Container(
            bgcolor=_COLOR_HDR,
            border_radius=ft.border_radius.only(top_left=4, top_right=4),
            padding=ft.padding.symmetric(horizontal=6, vertical=7),
            width=w_hor,
            content=ft.Row([
                ft.Container(width=_W_DIA, content=ft.Text(
                    "Día", color=Colores.BLANCO, size=12,
                    font_family=Fuentes.CAMPOS, weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER)),
                ft.Container(width=_W_HORA, content=ft.Text(
                    "Hora inicio", color=Colores.BLANCO, size=12,
                    font_family=Fuentes.CAMPOS, weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER)),
                ft.Container(width=_W_HORA, content=ft.Text(
                    "Hora final", color=Colores.BLANCO, size=12,
                    font_family=Fuentes.CAMPOS, weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER)),
            ], spacing=8),
        )

        btn_add_fila = ft.ElevatedButton(
            text="+",
            on_click=lambda _: self._agregar_fila(),
            bgcolor=_COLOR_HDR, color=Colores.BLANCO,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=4),
                padding=ft.padding.all(0),
                text_style=ft.TextStyle(
                    size=18, weight=ft.FontWeight.BOLD),
            ),
            width=30, height=28, elevation=0,
        )

        horario_footer = ft.Container(
            bgcolor=_COLOR_HDR,
            border_radius=ft.border_radius.only(
                bottom_left=4, bottom_right=4),
            padding=ft.padding.symmetric(horizontal=12, vertical=7),
            width=w_hor,
            content=ft.Row([
                ft.Text("Total", color=Colores.BLANCO, size=13,
                        font_family=Fuentes.CAMPOS,
                        weight=ft.FontWeight.W_600),
                self._lbl_total,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

        col1 = ft.Column(
            spacing=4,
            controls=[
                _lbl("Semestre"),
                self._dd_semestre,
                ft.Container(height=8),
                _lbl("Horario"),
                horario_header,
                self._col_horarios,
                btn_add_fila,
                horario_footer,
            ],
        )

        # ════════════════════ COL 2 ════════════════════════════
        # -- Unidad de aprendizaje: dropdown con lupa y buscador --
        # La lupa se coloca junto a la etiqueta (fuera del dropdown)
        # para que el on_click funcione correctamente en Flet 0.28.
        self._unidad_all_opts: list[ft.dropdown.Option] = []  # copia maestra
        self._buscando_unidad = False

        self._btn_buscar_unidad = ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_color=Colores.AZUL_PRIMARIO,
            icon_size=18,
            on_click=self._toggle_buscar_unidad,
            tooltip="Buscar unidad de aprendizaje",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.all(4),
                bgcolor=ft.Colors.with_opacity(0.08, Colores.AZUL_PRIMARIO),
            ),
        )
        # Etiqueta + lupa en la misma fila
        self._lbl_unidad_row = ft.Row(
            controls=[
                _lbl("Unidad de aprendizaje"),
                self._btn_buscar_unidad,
            ],
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._dd_unidad = ft.Dropdown(
            hint_text="Seleccionar unidad",
            options=[], disabled=True,
            on_change=self._on_unidad_cambiada,
            menu_height=150,   # menú compacto con scroll
            **_dd_kw(_W_UA),
        )
        # Buscador con lista de resultados scrollable (POO)
        self._buscador_unidad = _BuscadorUnidad(
            width=_W_UA,
            on_seleccionar=self._on_unidad_seleccionada,
            on_cerrar=self._toggle_buscar_unidad,
        )
        self._unidad_stack = ft.Stack(
            controls=[self._dd_unidad, self._buscador_unidad],
            width=_W_UA,
        )

        self._ctrl_aula = _DropdownConNuevo(
            hint_text="Seleccionar aula",
            opciones_iniciales=self._opts_aula(),
            width=_W_AULA,
            on_crear=self._crear_aula,
        )

        self._campo_periodo = ft.TextField(
            **_tf_kw(_W_PER, hint="Ej: Feb-Jun 2024"),
        )

        # ════════════════════ COL 3 ════════════════════════════

        self._tipo_txt = ft.Text(
            "", size=13, color=_NEGRO,
            font_family=Fuentes.CAMPOS,
        )
        tipo_contenedor = ft.Container(
            content=self._tipo_txt,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=6,
            bgcolor=Colores.BLANCO,
            padding=ft.padding.symmetric(horizontal=10, vertical=10),
            width=220,
        )

        # Calcular ancho del docente según el nombre más largo
        _max_doc_chars = max(
            (len(d.nombre) for d in self._docentes), default=20
        )
        # ~7.5px por carácter + padding (40px) + ícono dropdown (30px)
        _W_DOC_AUTO = max(_W_DOC, min(int(_max_doc_chars * 7.5) + 70, 400))
        self._ctrl_docente = _DropdownConNuevo(
            hint_text="Seleccionar docente",
            opciones_iniciales=self._opts_docente(),
            width=_W_DOC_AUTO,
            on_crear=self._crear_docente,
        )
        self._w_doc_auto = _W_DOC_AUTO  # guardar para el botón

        # ════════════════════ BOTONES ═════════════════════════
        _W_BTN_FIJO = 220  # ancho fijo para botones (no auto-ajustable)

        # Botón "+ Agregar" — siempre debajo de Docente
        self._btn_accion = ft.ElevatedButton(
            text="+ Agregar",
            on_click=self._on_btn_accion,
            bgcolor=Colores.AZUL_PRIMARIO, color=Colores.BLANCO,
            width=_W_BTN_FIJO,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=40, vertical=14),
                text_style=ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
            elevation=0,
        )

        # Botón "Guardar" — solo en modo edición, debajo de Periodo
        self._btn_guardar = ft.ElevatedButton(
            text="Guardar",
            on_click=lambda _: self._guardar_edicion(),
            bgcolor=Colores.AZUL_PRIMARIO, color=Colores.BLANCO,
            width=_W_BTN_FIJO,
            visible=False,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=40, vertical=14),
                text_style=ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
            elevation=0,
        )

        # Botón "Cancelar" — solo en modo edición, debajo de Periodo
        self._btn_cancelar = ft.ElevatedButton(
            text="Cancelar",
            on_click=lambda _: self._confirmar_cancelar_edicion(),
            width=_W_BTN_FIJO,
            visible=False,
            bgcolor=Colores.ROJO,
            color=Colores.BLANCO,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
                text_style=ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
            elevation=0,
        )

        # ════════════════════ COLUMNAS ═════════════════════════

        # UA más ancho: cubre su propio espacio + el de Docente
        # UA ocupa el ancho completo (UA + gap + Aulas)
        _W_UA_WIDE = _W_UA + 50 + _W_AULA
        self._dd_unidad.width        = _W_UA_WIDE
        self._buscador_unidad.set_width(_W_UA_WIDE)
        self._unidad_stack.width     = _W_UA_WIDE

        col2 = ft.Column(
            spacing=4,
            controls=[
                self._lbl_unidad_row,
                self._unidad_stack,
                ft.Container(height=8),
                # Tipo | Aulas — en la misma fila
                ft.Row(
                    controls=[
                        ft.Column(spacing=4, controls=[_lbl("Tipo"), tipo_contenedor]),
                        ft.Column(spacing=4, controls=[_lbl("Aulas"), self._ctrl_aula]),
                    ],
                    spacing=18,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=8),
                # Periodo + Guardar | Docente + Agregar/Cancelar
                ft.Row(
                    controls=[
                        ft.Column(
                            spacing=6,
                            controls=[
                                _lbl("Periodo"),
                                self._campo_periodo,
                                self._btn_guardar,
                            ],
                        ),
                        ft.Column(
                            spacing=6,
                            controls=[
                                _lbl("Docente"),
                                self._ctrl_docente,
                                self._btn_accion,
                                self._btn_cancelar,
                            ],
                        ),
                    ],
                    spacing=18,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
        )

        col3 = ft.Column(controls=[], spacing=0)  # vacío – todo en col2

        # ════════════════════ FORMULARIO ══════════════════════
        formulario = ft.Container(
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(
                left=_PAD_H, right=_PAD_H, top=12, bottom=16),
            content=ft.Row(
                controls=[col1, col2],
                spacing=50,
                alignment = ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        # ════════════════════ TABLA REGISTRADA ════════════════
        self._tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(
                    c, size=11, weight=ft.FontWeight.W_600,
                    font_family=Fuentes.CAMPOS, color=Colores.BLANCO))
                for c in ["Clave","Semestre","Unidad de aprendizaje",
                           "Docente","Horas","Aula","Periodo","Acción"]
            ],
            rows=[],
            heading_row_color=Colores.AZUL_PRIMARIO,
            heading_row_height=36,
            data_row_max_height=36,
            column_spacing=12,
            horizontal_margin=10,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=6,
            expand=True,          
        )

        panel_tabla = ft.Container(
            bgcolor=Colores.BLANCO,
            border=ft.border.all(1.5, Colores.BORDE),
            border_radius=8,
            margin=ft.margin.only(
                left=_PAD_H, right=_PAD_H, top=10, bottom=12),
            padding=ft.padding.all(14),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self._tabla],
                        expand=True,
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        controls=[
                            ft.OutlinedButton(
                                text="Visualizar documento",
                                icon=ft.Icons.DESCRIPTION_OUTLINED,
                                icon_color=Colores.AZUL_PRIMARIO,
                                on_click=self._visualizar,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                    padding=ft.padding.symmetric(
                                        horizontal=20, vertical=10),
                                    side=ft.BorderSide(
                                        1.5, Colores.AZUL_PRIMARIO),
                                    color=Colores.AZUL_PRIMARIO,
                                    text_style=ft.TextStyle(
                                        size=13,
                                        font_family=Fuentes.BOTONES),
                                ),
                            ),
                            ft.ElevatedButton(
                                text="Descargar",
                                icon=ft.Icons.DOWNLOAD,
                                on_click=self._descargar,
                                bgcolor=Colores.AZUL_PRIMARIO,
                                color=Colores.BLANCO,
                                elevation=0,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=6),
                                    padding=ft.padding.symmetric(
                                        horizontal=30, vertical=10),
                                    text_style=ft.TextStyle(
                                        size=13,
                                        font_family=Fuentes.BOTONES),
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,        
        )

        # ════════════════════ ENSAMBLADO ══════════════════════
        header = _Cabecera(on_cerrar=lambda _: self._volver())

        sub_header = ft.Container(
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(left=16, top=10, bottom=2),
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=Colores.AZUL_PRIMARIO,
                    icon_size=20,
                    on_click=lambda _: self._volver(),
                    tooltip="Volver",
                ),
                ft.Text(
                    f"Plan de estudios - {nombre_plan}",
                    size=20, weight=ft.FontWeight.W_400,
                    color=Colores.TEXTO,
                    font_family=Fuentes.TITULO,
                ),
            ], spacing=2,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

        lies_container = ft.Container(
            content=lies_row,
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(left=_PAD_H, top=6, bottom=8),
        )

        separador = ft.Divider(height=1, color=Colores.BORDE)

        contenido_scroll = ft.Column(
            controls=[
                sub_header,
                lies_container,
                separador,
                formulario,
                panel_tabla,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        super().__init__(
            controls=[header, contenido_scroll],
            spacing=0,
            expand=True,
        )

    # ── Ciclo de vida ─────────────────────────────────────────

    def did_mount(self) -> None:
        # Agregar FilePicker al overlay (sin duplicar)
        if self._save_picker not in self._page.overlay:
            self._page.overlay.append(self._save_picker)
            self._page.update()
        # Si viene desde historial, precargar los horarios del plan generado
        if self._id_plan_generado_precarga is not None:
            self._precargar_horarios(self._id_plan_generado_precarga)

    # ── Precarga de horarios desde historial ─────────────────

    def _precargar_horarios(self, id_plan_generado: int) -> None:
        """Precarga los IDs de horarios de un plan_generado en la sesión
        para que aparezcan en la tabla con editar/eliminar funcionales."""
        registros = self._service.obtener_horarios_de_plan_generado(id_plan_generado)
        if not registros:
            return
        # Agregar todos los IDs a la sesión
        for r in registros:
            self._state.ids_sesion.add(r.id_horario)
        # Auto-seleccionar el primer semestre que tenga horarios
        if self._semestres and not self._dd_semestre.value:
            # Buscar qué semestres tienen horarios precargados
            sems_con_datos = {r.numero_semestre for r in registros if r.numero_semestre > 0}
            sem_target = None
            for s in self._semestres:
                if s.numero in sems_con_datos:
                    sem_target = s
                    break
            if sem_target is None:
                sem_target = self._semestres[0]
            self._dd_semestre.value = str(sem_target.id)
            if self.page:
                self._dd_semestre.update()
            self._on_semestre_cambiado(None)
            # Restaurar ids_sesion ya que _on_semestre_cambiado la limpia
            for r in registros:
                self._state.ids_sesion.add(r.id_horario)
        # Recargar tabla con los horarios precargados
        self._recargar_tabla()

    # ── Builders de opciones ──────────────────────────────────

    def _opts_aula(self) -> list[ft.dropdown.Option]:
        return ([_opcion(str(a.id), a.nombre) for a in self._aulas]
                + [_opcion_nuevo()])

    def _opts_docente(self) -> list[ft.dropdown.Option]:
        return ([_opcion(str(d.id), d.nombre) for d in self._docentes]
                + [_opcion_nuevo()])

    # ── LIES ──────────────────────────────────────────────────

    def _on_lies_cambiado(self, lid: int, lnombre: str) -> None:
        self._id_lies_activa = lid
        self._state.id_lies_activa = lid
        for btn in self._lies_btns:
            activo = btn.text == lnombre
            btn.style.bgcolor = (Colores.AZUL_PRIMARIO if activo
                                 else "transparent")
            btn.style.color   = (Colores.BLANCO if activo
                                 else Colores.AZUL_PRIMARIO)
            if self.page:
                btn.update()
        # Limpiar tabla y sesión al cambiar de LIES
        # (el caché de tronco persiste entre LIES — correcto)
        self._tabla.rows = []
        self._state.limpiar_sesion()
        if self.page:
            self._tabla.update()
        if self._dd_semestre.value:
            self._on_semestre_cambiado(None)

    # ── Semestre → cargar unidades ────────────────────────────

    def _on_semestre_cambiado(self, _) -> None:
        id_sem = self._dd_semestre.value
        if not id_sem:
            return
        lid = self._id_lies_activa

        unidades = list(self._service.obtener_unidades(
            self._id_plan, lid, int(id_sem)))
        if self._sem_opt:
            unidades += self._service.obtener_unidades(
                self._id_plan, lid, self._sem_opt.id)

        unidades.sort(key=lambda u: (
            0 if u.tipo.lower().startswith("tronco") else 1, u.nombre))
        self._unidades = unidades

        opts = [_opcion(str(u.id_asignacion), u.nombre) for u in unidades]
        self._unidad_all_opts = list(opts)  # copia maestra para filtrar
        self._dd_unidad.options  = opts
        self._dd_unidad.value    = None
        self._dd_unidad.disabled = not unidades
        self._tipo_txt.value     = ""

        # Sincronizar opciones con el buscador
        self._buscador_unidad.set_opciones([
            (str(u.id_asignacion), u.nombre) for u in unidades
        ])

        # Resetear búsqueda si estaba activa
        if self._buscando_unidad:
            self._buscando_unidad = False
            self._buscador_unidad.desactivar()
            self._dd_unidad.visible = True
            self._btn_buscar_unidad.visible = True

        # Limpiar tabla y sesión al cambiar de semestre
        self._tabla.rows = []
        self._state.limpiar_todo()

        if self.page:
            self._page.update()

    # ── Unidad → auto tipo (texto plano, solo lectura) ────────

    def _on_unidad_cambiada(self, _) -> None:
        id_asig = self._dd_unidad.value
        if not id_asig:
            return
        u = next((u for u in self._unidades
                   if str(u.id_asignacion) == id_asig), None)
        if u:
            self._tipo_txt.value = u.tipo   # "Tronco" o "Optativa"
            if self.page:
                self._tipo_txt.update()

    # ── Buscar unidad de aprendizaje ──────────────────────────

    def _toggle_buscar_unidad(self, _) -> None:
        """Alterna entre dropdown+lupa y buscador con lista de resultados."""
        self._buscando_unidad = not self._buscando_unidad
        if self._buscando_unidad:
            # Ocultar Dropdown + lupa, activar buscador
            self._dd_unidad.visible = False
            self._btn_buscar_unidad.visible = False
            self._buscador_unidad.activar()
            if self.page:
                self._dd_unidad.update()
                self._btn_buscar_unidad.update()
        else:
            # Restaurar Dropdown + lupa, desactivar buscador
            self._buscador_unidad.desactivar()
            self._dd_unidad.visible = True
            self._btn_buscar_unidad.visible = True
            self._dd_unidad.options = list(self._unidad_all_opts)
            self._dd_unidad.value = None
            if self.page:
                self._dd_unidad.update()
                self._btn_buscar_unidad.update()

    def _on_unidad_seleccionada(self, key: str, text: str) -> None:
        """Callback del buscador: selecciona la unidad y cierra la búsqueda."""
        # Cerrar búsqueda
        self._buscando_unidad = False
        self._buscador_unidad.desactivar()
        self._dd_unidad.visible = True
        self._btn_buscar_unidad.visible = True
        self._dd_unidad.options = list(self._unidad_all_opts)
        self._dd_unidad.value = key
        if self.page:
            self._dd_unidad.update()
            self._btn_buscar_unidad.update()
        # Actualizar el campo de tipo
        u = next((u for u in self._unidades
                   if str(u.id_asignacion) == key), None)
        if u:
            self._tipo_txt.value = u.tipo
            if self.page:
                self._tipo_txt.update()

    # ── Crear aula nueva ──────────────────────────────────────

    def _crear_aula(self, nombre: str) -> None:
        dto = self._service.crear_aula(nombre)
        if dto is None:
            self._msg("No se pudo crear el aula (¿ya existe?).")
            self._ctrl_aula.restaurar_dd(None)
            return
        self._aulas.append(dto)
        self._ctrl_aula.reconstruir_opciones(
            self._opts_aula(), seleccion=str(dto.id))
        self._ctrl_aula.restaurar_dd(str(dto.id))

    # ── Crear docente nuevo ───────────────────────────────────

    def _crear_docente(self, nombre: str) -> None:
        dto = self._service.crear_docente(nombre)
        if dto is None:
            self._msg("No se pudo crear el docente (¿ya existe?).")
            self._ctrl_docente.restaurar_dd(None)
            return
        self._docentes.append(dto)
        self._ctrl_docente.reconstruir_opciones(
            self._opts_docente(), seleccion=str(dto.id))
        self._ctrl_docente.restaurar_dd(str(dto.id))

    # ── Filas de horario ──────────────────────────────────────

    def _agregar_fila(self) -> None:
        fila = _FilaHorario(
            on_quitar=self._quitar_fila,
            on_change=self._actualizar_total,
        )
        self._filas_horario.append(fila)
        self._col_horarios.controls.append(fila)
        if self.page:
            self._col_horarios.update()

    def _quitar_fila(self, fila: _FilaHorario) -> None:
        if len(self._filas_horario) <= 1:
            return
        self._filas_horario.remove(fila)
        self._col_horarios.controls.remove(fila)
        self._actualizar_total(None)
        if self.page:
            self._col_horarios.update()

    def _actualizar_total(self, _) -> None:
        total = 0
        for f in self._filas_horario:
            hi, hf = f.hora_inicio.get_24h(), f.hora_fin.get_24h()
            try:
                t0 = datetime.strptime(hi, "%H:%M")
                t1 = datetime.strptime(hf, "%H:%M")
                total += max(0, (t1 - t0).seconds) / 3600
            except ValueError:
                pass
        n = int(total)
        self._lbl_total.value = f"{n} Hora{'s' if n != 1 else ''}"
        if self.page:
            try:
                self._lbl_total.update()
            except Exception:
                pass

    # ── Botón de acción (Agregar / Guardar) ────────────────────

    def _on_btn_accion(self, _) -> None:
        try:
            self._agregar()
        except Exception as ex:
            self._msg(f"Error inesperado: {ex}")

    # ── Extract: validar campos del formulario ─────────────

    def _validar_campos_formulario(self) -> tuple | None:
        """Valida los campos comunes del formulario.
        Retorna (id_asig, id_aula, id_doc, periodo_txt) o None si hay error."""
        id_asig     = self._dd_unidad.value
        id_aula     = self._ctrl_aula.value
        id_doc      = self._ctrl_docente.value
        periodo_txt = (self._campo_periodo.value or "").strip()

        if not id_asig:
            self._msg("Selecciona una unidad de aprendizaje."); return None
        if not id_aula or id_aula == _KEY_NUEVO:
            self._msg("Selecciona un aula."); return None
        if not id_doc or id_doc == _KEY_NUEVO:
            self._msg("Selecciona un docente."); return None
        if not periodo_txt:
            self._msg("Escribe el periodo."); return None
        return id_asig, id_aula, id_doc, periodo_txt

    # ── Extract: recopilar filas válidas del formulario ──────

    def _recopilar_filas_validas(self) -> list[FilaHorarioDTO] | None:
        """Recoge las filas válidas del formulario de horario.
        Retorna lista de FilaHorarioDTO o None si hay error de validación."""
        filas: list[FilaHorarioDTO] = []
        for fila in self._filas_horario:
            dia = (fila.dd_dia.value or "").strip()
            if not dia:
                continue
            hi = fila.hora_inicio.get_24h()
            hf = fila.hora_fin.get_24h()
            try:
                t0 = datetime.strptime(hi, "%H:%M")
                t1 = datetime.strptime(hf, "%H:%M")
                delta = max(0, (t1 - t0).seconds) // 3600
            except ValueError:
                self._msg(f"Formato inválido: {hi} – {hf}"); return None
            filas.append(FilaHorarioDTO(dia=dia, hora_inicio=hi, hora_fin=hf, delta=delta))
        if not filas:
            self._msg("Completa al menos un horario (día + horas)."); return None
        return filas

    # ── Guardar horario (nuevo) ───────────────────────────────

    def _agregar(self) -> None:
        campos = self._validar_campos_formulario()
        if campos is None:
            return
        id_asig, id_aula, id_doc, periodo_txt = campos

        periodo_dto = self._service.crear_periodo(periodo_txt)
        if periodo_dto is None:
            self._msg("Error al registrar el periodo."); return

        # ── Tipo de materia y semestre ─────────────────────────
        id_materia = self._service.obtener_id_materia(int(id_asig))
        es_tronco  = id_materia is not None
        id_sem     = int(self._dd_semestre.value) if self._dd_semestre.value else None

        # ── Recopilar filas válidas ────────────────────────────
        filas_validas = self._recopilar_filas_validas()
        if filas_validas is None:
            return

        # ── Validación de tronco común (por semestre) ──────────
        error = self._state.validar_horario(
            es_tronco, id_materia, id_sem, filas_validas,
            id_aula=int(id_aula), id_docente=int(id_doc),
        )
        if error:
            self._msg(error); return

        # ── Guardar cada fila ─────────────────────────────────
        ids_nuevos = []
        for f in filas_validas:
            ok, msg, id_nuevo = self._service.guardar_horario(GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=f.dia, hora_inicio=f.hora_inicio,
                hora_fin=f.hora_fin,
                total_horas=f.delta, id_plan=self._id_plan,
                id_lies=self._id_lies_activa,
                id_semestre=id_sem,
            ))
            if not ok:
                self._msg(msg); return
            if id_nuevo is not None:
                self._state.ids_sesion.add(id_nuevo)
                ids_nuevos.append(id_nuevo)

        # ── Actualizar caché de tronco u optativa ─────────────
        if es_tronco and id_materia is not None and id_sem is not None:
            self._state.registrar_tronco(
                id_sem, id_materia, filas_validas,
                id_lies=self._id_lies_activa,
                id_aula=int(id_aula),
                id_docente=int(id_doc),
            )
        elif not es_tronco and id_sem is not None:
            for fila_d, id_h in zip(filas_validas, ids_nuevos):
                self._state.registrar_optativa(
                    self._id_lies_activa, id_sem, [fila_d], id_h)

        self._msg("¡Horario agregado correctamente!")
        self._recargar_tabla()
        self._limpiar_formulario()


    # ── Edición: iniciar ──────────────────────────────────────

    def _iniciar_edicion(self, id_horario: int) -> None:
        """Carga los datos del horario en los campos del formulario.
        Preserva la tabla y los IDs de sesión durante la edición."""
        detalle = self._service.obtener_horario_detalle(id_horario)
        if detalle is None:
            self._msg("No se encontró el horario."); return

        self._state.editando_id = id_horario

        # 1. Semestre — cargar unidades SIN limpiar tabla/sesión
        self._dd_semestre.value = str(detalle.id_semestre)
        if self.page:
            self._dd_semestre.update()
        # Cargar unidades sin borrar la tabla ni los IDs de sesión
        self._cargar_unidades_sin_limpiar(str(detalle.id_semestre))

        # 2. Unidad de aprendizaje
        self._dd_unidad.value = str(detalle.id_asignacion)
        if self.page:
            self._dd_unidad.update()
        # Auto-tipo
        self._on_unidad_cambiada(None)

        # 3. Aula
        self._ctrl_aula.value = str(detalle.id_aula)

        # 4. Docente
        self._ctrl_docente.value = str(detalle.id_docente)

        # 5. Periodo
        self._campo_periodo.value = detalle.periodo_nombre
        if self.page:
            self._campo_periodo.update()

        # 6. Horario (día + horas) – usar la primera fila
        # Limpiar filas extra y dejar solo una
        while len(self._filas_horario) > 1:
            f = self._filas_horario.pop()
            self._col_horarios.controls.remove(f)
        fila = self._filas_horario[0]
        fila.dd_dia.value = detalle.dia
        if self.page:
            fila.dd_dia.update()
        fila.hora_inicio.set_from_24h(detalle.hora_inicio)
        fila.hora_fin.set_from_24h(detalle.hora_fin)
        self._actualizar_total(None)

        # 7. Ocultar "+ Agregar", mostrar "Guardar" + "Cancelar"
        self._btn_accion.visible = False
        self._btn_guardar.visible = True
        self._btn_cancelar.visible = True
        if self.page:
            self.update()

    def _cargar_unidades_sin_limpiar(self, id_sem: str) -> None:
        """Carga las unidades de aprendizaje para el semestre dado
        SIN limpiar la tabla ni los IDs de sesión."""
        if not id_sem:
            return
        lid = self._id_lies_activa

        unidades = list(self._service.obtener_unidades(
            self._id_plan, lid, int(id_sem)))
        if self._sem_opt:
            unidades += self._service.obtener_unidades(
                self._id_plan, lid, self._sem_opt.id)

        unidades.sort(key=lambda u: (
            0 if u.tipo.lower().startswith("tronco") else 1, u.nombre))
        self._unidades = unidades

        opts = [_opcion(str(u.id_asignacion), u.nombre) for u in unidades]
        self._unidad_all_opts = list(opts)
        self._dd_unidad.options  = opts
        self._dd_unidad.value    = None
        self._dd_unidad.disabled = not unidades
        self._tipo_txt.value     = ""

        if self.page:
            self._dd_unidad.update()
            self._tipo_txt.update()

    # ── Edición: confirmar cancelar ────────────────────────────

    def _confirmar_cancelar_edicion(self) -> None:
        """Muestra diálogo ¿Estás seguro? antes de cancelar la edición."""
        self._page.open(DialogoConfirmacion(
            page=self._page,
            on_confirmar=lambda: self._cancelar_edicion(),
        ))

    # ── Edición: cancelar ─────────────────────────────────────

    def _cancelar_edicion(self) -> None:
        """Restaura el formulario al modo agregar, conservando la tabla y el semestre."""
        self._state.editando_id = None

        # Restaurar botones: mostrar "+ Agregar", ocultar "Guardar" y "Cancelar"
        self._btn_accion.visible = True
        self._btn_guardar.visible = False
        self._btn_cancelar.visible = False

        # Limpiar campos del formulario (NO el semestre para conservar la tabla)
        self._post_agregar_cleanup()

        # Mostrar las materias de la sesión actual en la tabla
        self._recargar_tabla()

    # ── Edición: guardar cambios ──────────────────────────────

    def _guardar_edicion(self) -> None:
        """Guarda los cambios del horario en edición.
        Soporta múltiples filas: actualiza el registro original con la primera
        fila y crea nuevos registros para las filas adicionales."""
        campos = self._validar_campos_formulario()
        if campos is None:
            return
        id_asig, id_aula, id_doc, periodo_txt = campos

        periodo_dto = self._service.crear_periodo(periodo_txt)
        if periodo_dto is None:
            self._msg("Error al registrar el periodo."); return

        # ── Recopilar TODAS las filas válidas ────────────────────
        filas_validas = self._recopilar_filas_validas()
        if filas_validas is None:
            return

        # ── Validación de tronco común (por semestre) ──────────
        id_materia = self._service.obtener_id_materia(int(id_asig))
        es_tronco  = id_materia is not None
        id_sem     = int(self._dd_semestre.value) if self._dd_semestre.value else None

        error = self._state.validar_horario(
            es_tronco, id_materia, id_sem, filas_validas,
            id_horario_excluir=self._state.editando_id,
            id_aula=int(id_aula), id_docente=int(id_doc),
        )
        if error:
            self._msg(error); return

        # ── Actualizar el registro original con la primera fila ──
        f0 = filas_validas[0]
        ok, msg = self._service.actualizar_horario(
            id_horario=self._state.editando_id,
            dto=GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=f0.dia, hora_inicio=f0.hora_inicio,
                hora_fin=f0.hora_fin,
                total_horas=f0.delta, id_plan=self._id_plan,
                id_lies=self._id_lies_activa,
                id_semestre=id_sem,
            ),
        )

        if not ok:
            self._msg(msg)
            self._cancelar_edicion()
            return

        # ── Crear registros nuevos para filas adicionales ───────
        for f in filas_validas[1:]:
            ok_n, msg_n, id_nuevo = self._service.guardar_horario(GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=f.dia, hora_inicio=f.hora_inicio,
                hora_fin=f.hora_fin,
                total_horas=f.delta, id_plan=self._id_plan,
                id_lies=self._id_lies_activa,
                id_semestre=id_sem,
            ))
            if not ok_n:
                self._msg(msg_n); break
            if id_nuevo is not None:
                self._state.ids_sesion.add(id_nuevo)

        # ── Actualizar caché de tronco u optativa ─────────────
        if es_tronco and id_materia is not None and id_sem is not None:
            self._state.registrar_tronco(
                id_sem, id_materia, filas_validas,
                id_lies=self._id_lies_activa,
                id_aula=int(id_aula),
                id_docente=int(id_doc),
            )
        elif not es_tronco and id_sem is not None and self._state.editando_id is not None:
            self._state.actualizar_optativa(
                self._id_lies_activa, id_sem, filas_validas, self._state.editando_id)

        self._msg("¡Horario actualizado correctamente!")
        self._cancelar_edicion()
        self._state.reconstruir_caches(self._dd_semestre.value)

    # ── Limpieza de formulario ─────────────────────────────────

    def _limpiar_formulario(self) -> None:
        """Reinicia los campos del formulario al estado vacío.

        NO limpia el semestre ni la tabla porque este método se invoca
        justo después de ``_recargar_tabla()`` en ``_agregar()`` y
        ``_guardar_edicion()``; borrarlos aquí eliminaría los datos
        recién cargados.
        """
        self._post_agregar_cleanup()

    def _post_agregar_cleanup(self) -> None:
        """Capa de restauración visual post-acción.

        Limpia inputs, reinicia dropdowns dependientes y fuerza
        repaint. NO toca lógica de negocio.
        """
        # Reiniciar dropdown de unidad con repaint forzado
        self._dd_unidad = reset_dropdown(
            self._dd_unidad,
            options=list(self._unidad_all_opts),
            disabled=not self._unidad_all_opts,
        )
        self._ctrl_aula.reset()
        self._ctrl_docente.reset()
        self._campo_periodo.value = ""
        self._tipo_txt.value = ""

        # Restaurar horario a una sola fila vacía
        while len(self._filas_horario) > 1:
            fila = self._filas_horario.pop()
            self._col_horarios.controls.remove(fila)

        fila = self._filas_horario[0]
        fila.dd_dia = reset_dropdown(fila.dd_dia)
        fila.hora_inicio.set_from_24h("07:00")
        fila.hora_fin.set_from_24h("08:00")
        self._actualizar_total(None)

        if self.page:
            self._page.update()

    # ── Reconstrucción de cachés (delegado al state) ──────────

    def _reconstruir_caches(self) -> None:
        """Delegación a HorarioStateManager."""
        self._state.reconstruir_caches(self._dd_semestre.value)

    # ── Tabla inferior ────────────────────────────────────────

    def _recargar_tabla(self) -> None:
        """Recarga la tabla mostrando ÚNICAMENTE los horarios creados en esta sesión."""
        try:
            if not self._state.ids_sesion:
                self._tabla.rows = []
                if self.page:
                    self._tabla.update()
                return
            id_sem = self._dd_semestre.value
            if not id_sem:
                self._tabla.rows = []
                if self.page:
                    self._tabla.update()
                return
            todos = self._service.obtener_horarios_filtrados(
                id_plan=self._id_plan,
                id_lies=self._id_lies_activa,
                id_semestre=int(id_sem),
                id_semestre_opt=self._sem_opt.id if self._sem_opt else None,
            )
            registros = [r for r in todos if r.id_horario in self._state.ids_sesion]
            # Re-numerar claves desde 001
            self._tabla.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(i).zfill(3), size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Text(r.semestre, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Text(r.unidad, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Text(r.docente, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Text(str(r.total_horas), size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Text(r.aulas, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Text(r.periodo, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=Colores.AZUL_PRIMARIO,
                            icon_size=16, tooltip="Editar",
                            on_click=partial(self._on_editar_click, r.id_horario),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=Colores.ROJO,
                            icon_size=16, tooltip="Eliminar",
                            on_click=partial(self._on_eliminar_click, r.id_horario),
                        ),
                    ], spacing=0)),
                ])
                for i, r in enumerate(registros, start=1)
            ]
            if self.page:
                self._tabla.update()
        except Exception as ex:
            self._msg(f"Error al recargar tabla: {ex}")

    def _confirmar_eliminar(self, id_horario: int) -> None:
        """Muestra diálogo ¿Estás seguro? antes de eliminar."""
        self._page.open(DialogoConfirmacion(
            page=self._page,
            on_confirmar=lambda: self._eliminar(id_horario),
        ))

    def _on_editar_click(self, id_horario: int, _=None) -> None:
        """Wrapper para functools.partial en tabla."""
        self._iniciar_edicion(id_horario)

    def _on_eliminar_click(self, id_horario: int, _=None) -> None:
        """Wrapper para functools.partial en tabla."""
        self._confirmar_eliminar(id_horario)

    def _eliminar(self, id_horario: int) -> None:
        id_sem_actual = int(self._dd_semestre.value) if self._dd_semestre.value else None
        ok, msg = self._service.eliminar_horario(id_horario)
        self._msg(msg)
        if ok:
            self._state.ids_sesion.discard(id_horario)
            if id_sem_actual is not None:
                self._state.quitar_optativa(
                    self._id_lies_activa, id_sem_actual, id_horario)
            self._recargar_tabla()
            self._reconstruir_caches()

    # ── Helpers de PDF ─────────────────────────────────────────

    def _datos_para_pdf(self):
        """Retorna (registros, nombre_plan, lies_nombre, nombre_sem) o None.
        Usa SOLO los IDs de horarios creados en esta sesión.
        """
        id_sem = self._dd_semestre.value
        if not id_sem:
            self._msg("Selecciona un semestre antes de exportar.")
            return None
        if not self._state.ids_sesion:
            self._msg("No hay horarios en esta sesión para exportar. "
                      "Agrega al menos un horario primero.")
            return None
        # Obtener todos y filtrar solo los de sesión
        todos = self._service.obtener_horarios_filtrados(
            id_plan=self._id_plan,
            id_lies=self._id_lies_activa,
            id_semestre=int(id_sem),
            id_semestre_opt=self._sem_opt.id if self._sem_opt else None,
        )
        registros = [r for r in todos if r.id_horario in self._state.ids_sesion]
        if not registros:
            self._msg("No hay horarios de sesión para exportar.")
            return None
        nombre_plan = self._service.obtener_nombre_plan(self._id_plan)
        lies_nombre = ""
        for lies in self._all_lies:
            if lies.id == self._id_lies_activa:
                lies_nombre = lies.nombre
                break
        # Obtener nombre del semestre seleccionado
        nombre_sem = ""
        for s in self._semestres:
            if str(s.id) == id_sem:
                nombre_sem = f"Semestre {s.numero}"
                break
        return registros, nombre_plan, lies_nombre, nombre_sem

    def _generar_pdf(self, ruta: str) -> bool:
        """Genera el PDF en la ruta indicada. Retorna True si tuvo éxito."""
        datos = self._datos_para_pdf()
        if datos is None:
            return False
        registros, nombre_plan, lies_nombre, nombre_sem = datos
        try:
            GeneradorPDF(
                horarios=registros,
                nombre_plan=nombre_plan,
                nombre_lies=lies_nombre,
                ruta_membrete=self._ruta_membrete,
                ruta_salida=ruta,
                nombre_semestre=nombre_sem,
            ).generar()
            return True
        except Exception as e:
            self._msg(f"Error al generar PDF: {e}")
            return False

    # ── Vista previa (popup) ──────────────────────────────────

    def _visualizar(self, _=None) -> None:
        """Genera PDF temporal y muestra vista previa en un diálogo.
        Siempre regenera con los datos de sesión más recientes.
        """
        import time as _time
        _ts = int(_time.time())
        ruta = os.path.join(
            tempfile.gettempdir(),
            f"preview_{self._id_plan}_{self._id_lies_activa}_{_ts}.pdf",
        )
        if not self._generar_pdf(ruta):
            return

        try:
            import fitz  # PyMuPDF
            doc_pdf = fitz.open(ruta)
            page_pdf = doc_pdf[0]
            pix = page_pdf.get_pixmap(dpi=150)
            img_path = os.path.join(
                tempfile.gettempdir(),
                f"preview_{self._id_plan}_{self._id_lies_activa}_{_ts}.png",
            )
            pix.save(img_path)
            doc_pdf.close()

            dlg = ft.AlertDialog(
                modal=True,
                bgcolor=Colores.BLANCO,
                title=ft.Text(
                    "Vista previa del documento",
                    font_family=Fuentes.TITULO,
                    size=18,
                    color=Colores.AZUL_PRIMARIO,
                ),
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Image(
                                src=img_path,
                                fit=ft.ImageFit.CONTAIN,
                                width=550,
                            ),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=600,
                    height=550,
                    border=ft.border.all(1, Colores.AZUL_PRIMARIO),
                    border_radius=8,
                ),
                actions=[
                    ft.TextButton(
                        "Cerrar",
                        on_click=lambda _: self._page.close(dlg),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(radius=10),
            )
            self._page.open(dlg)
        except ImportError:
            # Si PyMuPDF no está instalado, abrir con el visor del sistema
            import subprocess, sys
            if sys.platform.startswith("win"):
                os.startfile(ruta)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
            self._msg("Vista previa abierta en el visor del sistema.")

    # ── Descarga con selección de ruta ─────────────────────────

    def _descargar(self, _=None) -> None:
        """Abre diálogo del sistema para elegir dónde guardar el PDF."""
        datos = self._datos_para_pdf()
        if datos is None:
            return
        self._save_picker.save_file(
            dialog_title="Guardar PDF de horario",
            file_name=f"horario_{self._id_plan}.pdf",
            allowed_extensions=["pdf"],
        )

    def _on_save_result(self, e: ft.FilePickerResultEvent) -> None:
        """Callback del FilePicker — genera el PDF en la ruta seleccionada."""
        if not e.path:
            return
        ruta = e.path
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"
        if self._generar_pdf(ruta):
            self._msg(f"PDF guardado en: {ruta}")

    # ── Navegación y mensajes ─────────────────────────────────

    def _volver(self) -> None:
        self._state.limpiar_completo()

        # Resetear semestre (no cubierto por _post_agregar_cleanup)
        self._dd_semestre = reset_dropdown(self._dd_semestre, disabled=False)

        # Limpiar formulario completo
        self._post_agregar_cleanup()

        # Restaurar botones al modo agregar
        self._btn_accion.visible = True
        self._btn_guardar.visible = False
        self._btn_cancelar.visible = False

        # Limpiar tabla
        self._tabla.rows = []

        # Remover FilePicker del overlay para no acumular
        if self._save_picker in self._page.overlay:
            self._page.overlay.remove(self._save_picker)
        if self._on_volver:
            self._on_volver()

    def _msg(self, texto: str) -> None:
        print(f"[DetallePlanView] {texto}")
        self._page.open(ft.SnackBar(content=ft.Text(texto)))