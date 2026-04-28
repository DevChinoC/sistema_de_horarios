import flet as ft
import os
import tempfile
from typing import Callable
from datetime import datetime

from application.services.horario_service import HorarioService
from application.dto.horario_dto import GuardarHorarioDTO
from ui.components.plan_components import Colores, Fuentes, DialogoConfirmacion
from ui.pdf.generador_pdf import GeneradorPDF

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
    ) -> None:
        self._page          = page
        self._id_plan       = id_plan
        self._service       = service
        self._on_volver     = on_volver
        # Cargar membrete desde la BD (prioritario) o parámetro de respaldo
        self._ruta_membrete = service.obtener_ruta_membrete(id_plan) or ruta_membrete

        # ── Estado de edición ─────────────────────────────────
        self._editando_id: int | None = None   # id_horario en edición

        # ── Caché en memoria de horas de tronco común (por sesión) ──
        # Estructura: {id_semestre: {id_materia: [{"dia", "hora_inicio", "hora_fin"}, ...]}}
        # Se resetea cada vez que se crea la vista (nueva sesión).
        self._tronco_horas: dict[int, dict[int, list[dict]]] = {}

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
            # MIIDT → el usuario selecciona la LIES activa
            self._id_lies_activa = self._all_lies[0].id
        else:
            # No MIIDT → tomar la primera LIES asociada al plan para queries
            _all = service.obtener_todas_lies_del_plan(id_plan)
            self._id_lies_activa = _all[0].id if _all else 0

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
        # -- Unidad de aprendizaje: dropdown con lupa y búsqueda --
        # La lupa aparece como ícono PREFIX (izquierda) del dropdown.
        # Al hacer clic en ella se muestra el TextField de filtrado.
        self._unidad_all_opts: list[ft.dropdown.Option] = []  # copia maestra
        self._buscando_unidad = False

        self._btn_buscar_unidad = ft.Container(
            content=ft.Icon(
                ft.Icons.SEARCH,
                color=Colores.AZUL_PRIMARIO,
                size=20,
            ),
            on_click=self._toggle_buscar_unidad,
            tooltip="Haz clic para buscar por nombre",
            ink=True,
            padding=ft.padding.all(4),
        )
        self._dd_unidad = ft.Dropdown(
            hint_text="Seleccionar unidad",
            options=[], disabled=True,
            on_change=self._on_unidad_cambiada,
            # Lupa al inicio (prefix) — clic la activa
            prefix=self._btn_buscar_unidad,
            max_menu_height=160,   # scroll cuando hay muchas materias
            **_dd_kw(_W_UA),
        )
        self._tf_buscar_unidad = ft.TextField(
            visible=False,
            on_change=self._on_buscar_unidad_change,
            on_blur=self._on_buscar_unidad_blur,
            prefix=ft.Icon(ft.Icons.SEARCH, color=Colores.AZUL_PRIMARIO, size=18),
            suffix=ft.Container(
                content=ft.Icon(
                    ft.Icons.CLOSE,
                    color=Colores.ROJO,
                    size=18,
                ),
                on_click=self._toggle_buscar_unidad,
                tooltip="Cerrar búsqueda",
                ink=True,
                padding=ft.padding.all(2),
            ),
            **_tf_kw(_W_UA, hint="Escriba para filtrar…"),
        )
        self._unidad_stack = ft.Stack(
            controls=[self._dd_unidad, self._tf_buscar_unidad],
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

        self._ctrl_docente = _DropdownConNuevo(
            hint_text="Seleccionar docente",
            opciones_iniciales=self._opts_docente(),
            width=_W_DOC,
            on_crear=self._crear_docente,
        )

        # ════════════════════ BOTONES ═════════════════════════

        self._btn_accion = ft.ElevatedButton(
            text="+ Agregar",
            on_click=self._on_btn_accion,
            bgcolor=Colores.AZUL_PRIMARIO, color=Colores.BLANCO,
            width=220,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=40, vertical=14),
                text_style=ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
            elevation=0,
        )

        self._btn_cancelar = ft.ElevatedButton(
            text="Cancelar",
            on_click=lambda _: self._confirmar_cancelar_edicion(),
            width=220,
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

        col2 = ft.Column(
            spacing=4,
            controls=[
                _lbl("Unidad de aprendizaje"),
                self._unidad_stack,
                ft.Container(height=8),
                _lbl("Aulas"),
                self._ctrl_aula,
                ft.Container(height=8),
                _lbl("Periodo"),
                self._campo_periodo,
                ft.Container(height=14),
                self._btn_accion,
            ],
        )

        col3 = ft.Column(
            spacing=4,
            controls=[
                _lbl("Tipo"),
                tipo_contenedor,
                ft.Container(height=8),
                _lbl("Docente"),
                self._ctrl_docente,
                ft.Container(height=108),
                self._btn_cancelar
            ],
        )

        # ════════════════════ FORMULARIO ══════════════════════
        formulario = ft.Container(
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(
                left=_PAD_H, right=_PAD_H, top=12, bottom=16),
            content=ft.Row(
                controls=[col1, col2, col3],
                spacing=50,
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
        # Tabla empieza vacía — no se carga historial anterior

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
        for btn in self._lies_btns:
            activo = btn.text == lnombre
            btn.style.bgcolor = (Colores.AZUL_PRIMARIO if activo
                                 else "transparent")
            btn.style.color   = (Colores.BLANCO if activo
                                 else Colores.AZUL_PRIMARIO)
            if self.page:
                btn.update()
        # Limpiar tabla al cambiar de LIES
        self._tabla.rows = []
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

        # Resetear búsqueda si estaba activa
        if self._buscando_unidad:
            self._buscando_unidad = False
            self._tf_buscar_unidad.visible = False
            self._tf_buscar_unidad.value = ""
            self._dd_unidad.visible = True
            if self.page:
                self._tf_buscar_unidad.update()
                self._dd_unidad.update()

        # Limpiar tabla al cambiar de semestre
        self._tabla.rows = []

        if self.page:
            self._dd_unidad.update()
            self._tipo_txt.update()
            self._tabla.update()

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
        """Alterna entre dropdown y campo de búsqueda en el mismo espacio."""
        self._buscando_unidad = not self._buscando_unidad
        if self._buscando_unidad:
            # Mostrar TextField, ocultar Dropdown
            self._dd_unidad.visible = False
            self._tf_buscar_unidad.visible = True
            self._tf_buscar_unidad.value = ""
            if self.page:
                self._dd_unidad.update()
                self._tf_buscar_unidad.update()
                self._tf_buscar_unidad.focus()
        else:
            # Restaurar Dropdown, ocultar TextField
            self._tf_buscar_unidad.visible = False
            self._dd_unidad.visible = True
            self._dd_unidad.options = list(self._unidad_all_opts)
            self._dd_unidad.value = None
            if self.page:
                self._tf_buscar_unidad.update()
                self._dd_unidad.update()

    def _on_buscar_unidad_blur(self, _) -> None:
        """Cierra búsqueda si el campo pierde foco sin texto."""
        if self._buscando_unidad and not (self._tf_buscar_unidad.value or "").strip():
            self._toggle_buscar_unidad(None)

    def _on_buscar_unidad_change(self, _) -> None:
        """Filtra las opciones del dropdown conforme el usuario escribe."""
        texto = (self._tf_buscar_unidad.value or "").strip().lower()
        if not texto:
            self._dd_unidad.options = list(self._unidad_all_opts)
        else:
            self._dd_unidad.options = [
                opt for opt in self._unidad_all_opts
                if texto in (opt.text or "").lower()
            ]
        self._dd_unidad.value = None
        self._dd_unidad.visible = True
        if self.page:
            self._dd_unidad.update()

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
            if self._editando_id is not None:
                self._guardar_edicion()
            else:
                self._agregar()
        except Exception as ex:
            self._msg(f"Error inesperado: {ex}")

    # ── Helper: validar tronco común (por semestre) ────────────

    def _validar_tronco(
        self,
        es_tronco: bool,
        id_materia: int | None,
        id_sem: int | None,
        filas: list[dict],
    ) -> str | None:
        """Valida reglas de tronco común.  Retorna mensaje de error o None.

        Reglas:
        1. Misma materia de tronco en otra LIES → mismos días y horas.
        2. Diferente materia de tronco → no puede usar el mismo rango horario.
        3. Optativa → no puede usar rango horario de tronco.
        4. Todo es por semestre; otro semestre no afecta.
        """
        if id_sem is None:
            return None
        sem_cache = self._tronco_horas.get(id_sem, {})

        if es_tronco and id_materia is not None:
            # ── Regla 1: misma materia → mismos días + horas ──
            if id_materia in sem_cache:
                existing = sem_cache[id_materia]
                ex_set = {
                    (h["dia"], h["hora_inicio"], h["hora_fin"])
                    for h in existing
                }
                new_set = {
                    (f["dia"], f["hora_inicio"], f["hora_fin"])
                    for f in filas
                }
                if ex_set != new_set:
                    dias_ex = ", ".join(sorted({h["dia"] for h in existing}))
                    h0 = existing[0]
                    return (
                        f"Esta materia de tronco común ya tiene horario "
                        f"asignado: {dias_ex} "
                        f"{h0['hora_inicio']}–{h0['hora_fin']}.\n"
                        f"Debes usar el mismo horario en todas las LIES."
                    )

            # ── Regla 2: otra materia de tronco → sin solapamiento ──
            for mat_id, mat_hrs in sem_cache.items():
                if mat_id == id_materia:
                    continue
                for h_ex in mat_hrs:
                    hi_ex = datetime.strptime(h_ex["hora_inicio"], "%H:%M")
                    hf_ex = datetime.strptime(h_ex["hora_fin"], "%H:%M")
                    for f in filas:
                        hi_n = datetime.strptime(f["hora_inicio"], "%H:%M")
                        hf_n = datetime.strptime(f["hora_fin"], "%H:%M")
                        if hi_n < hf_ex and hf_n > hi_ex:
                            return (
                                f"El rango {f['hora_inicio']}–{f['hora_fin']} "
                                f"colisiona con otra materia de tronco común "
                                f"({h_ex['hora_inicio']}–{h_ex['hora_fin']}).\n"
                                f"Las materias de tronco no pueden compartir "
                                f"rango horario en el mismo semestre."
                            )
        else:
            # ── Regla 3: optativa vs tronco → sin solapamiento ──
            for _mat_id, mat_hrs in sem_cache.items():
                for h_ex in mat_hrs:
                    hi_ex = datetime.strptime(h_ex["hora_inicio"], "%H:%M")
                    hf_ex = datetime.strptime(h_ex["hora_fin"], "%H:%M")
                    for f in filas:
                        hi_n = datetime.strptime(f["hora_inicio"], "%H:%M")
                        hf_n = datetime.strptime(f["hora_fin"], "%H:%M")
                        if hi_n < hf_ex and hf_n > hi_ex:
                            return (
                                f"El horario {f['hora_inicio']}–{f['hora_fin']} "
                                f"colisiona con una materia de tronco común "
                                f"({h_ex['hora_inicio']}–{h_ex['hora_fin']}).\n"
                                f"Las optativas no pueden compartir rango "
                                f"horario con materias de tronco común."
                            )
        return None

    def _registrar_tronco_cache(
        self, id_sem: int, id_materia: int, filas: list[dict],
    ) -> None:
        """Agrega las horas al caché de tronco (si la materia aún no existe)."""
        if id_sem not in self._tronco_horas:
            self._tronco_horas[id_sem] = {}
        if id_materia not in self._tronco_horas[id_sem]:
            self._tronco_horas[id_sem][id_materia] = [
                {"dia": f["dia"],
                 "hora_inicio": f["hora_inicio"],
                 "hora_fin": f["hora_fin"]}
                for f in filas
            ]

    # ── Guardar horario (nuevo) ───────────────────────────────

    def _agregar(self) -> None:
        id_asig     = self._dd_unidad.value
        id_aula     = self._ctrl_aula.value
        id_doc      = self._ctrl_docente.value
        periodo_txt = (self._campo_periodo.value or "").strip()

        if not id_asig:
            self._msg("Selecciona una unidad de aprendizaje."); return
        if not id_aula or id_aula == _KEY_NUEVO:
            self._msg("Selecciona un aula."); return
        if not id_doc or id_doc == _KEY_NUEVO:
            self._msg("Selecciona un docente."); return
        if not periodo_txt:
            self._msg("Escribe el periodo."); return

        periodo_dto = self._service.crear_periodo(periodo_txt)
        if periodo_dto is None:
            self._msg("Error al registrar el periodo."); return

        # ── Tipo de materia y semestre ─────────────────────────
        id_materia = self._service.obtener_id_materia(int(id_asig))
        es_tronco  = id_materia is not None
        id_sem     = int(self._dd_semestre.value) if self._dd_semestre.value else None

        # ── Recopilar filas válidas ────────────────────────────
        filas_validas: list[dict] = []
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
                self._msg(f"Formato inválido: {hi} – {hf}"); return
            filas_validas.append({
                "dia": dia, "hora_inicio": hi, "hora_fin": hf,
                "delta": delta,
            })

        if not filas_validas:
            self._msg("Completa al menos un horario (día + horas)."); return

        # ── Validación de tronco común (por semestre) ──────────
        error = self._validar_tronco(es_tronco, id_materia, id_sem, filas_validas)
        if error:
            self._msg(error); return

        # ── Guardar cada fila ─────────────────────────────────
        for f in filas_validas:
            ok, msg = self._service.guardar_horario(GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=f["dia"], hora_inicio=f["hora_inicio"],
                hora_fin=f["hora_fin"],
                total_horas=f["delta"], id_plan=self._id_plan,
            ))
            if not ok:
                self._msg(msg); return

        # ── Actualizar caché de tronco ─────────────────────────
        if es_tronco and id_materia is not None and id_sem is not None:
            self._registrar_tronco_cache(id_sem, id_materia, filas_validas)

        self._msg("¡Horario agregado correctamente!")
        self._recargar_tabla()

    # ── Edición: iniciar ──────────────────────────────────────

    def _iniciar_edicion(self, id_horario: int) -> None:
        """Carga los datos del horario en los campos del formulario."""
        detalle = self._service.obtener_horario_detalle(id_horario)
        if detalle is None:
            self._msg("No se encontró el horario."); return

        self._editando_id = id_horario

        # 1. Semestre
        self._dd_semestre.value = str(detalle.id_semestre)
        if self.page:
            self._dd_semestre.update()
        # Cargar unidades para ese semestre
        self._on_semestre_cambiado(None)

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

        # 7. Cambiar botón a "Guardar" + mostrar "Cancelar"
        self._btn_accion.text = "Guardar"
        self._btn_accion.bgcolor = Colores.AZUL_PRIMARIO
        self._btn_cancelar.visible = True
        if self.page:
            self._btn_accion.update()
            self._btn_cancelar.update()
            self._col_horarios.update()

    # ── Edición: confirmar cancelar ────────────────────────────

    def _confirmar_cancelar_edicion(self) -> None:
        """Muestra diálogo ¿Estás seguro? antes de cancelar la edición."""
        self._page.open(DialogoConfirmacion(
            page=self._page,
            on_confirmar=lambda: self._cancelar_edicion(),
        ))

    # ── Edición: cancelar ─────────────────────────────────────

    def _cancelar_edicion(self) -> None:
        """Restaura el formulario al modo agregar."""
        self._editando_id = None

        # Restaurar botón
        self._btn_accion.text = "+ Agregar"
        self._btn_accion.bgcolor = Colores.AZUL_PRIMARIO
        self._btn_cancelar.visible = False

        # Limpiar campos
        self._dd_semestre.value = None
        self._dd_unidad.options = []
        self._dd_unidad.value = None
        self._dd_unidad.disabled = True
        self._tipo_txt.value = ""
        self._ctrl_aula.value = None
        self._ctrl_docente.value = None
        self._campo_periodo.value = ""

        # Restaurar horario a una fila vacía
        while len(self._filas_horario) > 1:
            f = self._filas_horario.pop()
            self._col_horarios.controls.remove(f)
        fila = self._filas_horario[0]
        fila.dd_dia.value = None
        # Reset time pickers to defaults
        fila.hora_inicio.set_from_24h("01:00")
        fila.hora_fin.set_from_24h("01:00")
        self._actualizar_total(None)

        if self.page:
            self._btn_accion.update()
            self._btn_cancelar.update()
            self._dd_semestre.update()
            self._dd_unidad.update()
            self._tipo_txt.update()
            self._campo_periodo.update()
            fila.dd_dia.update()
            self._col_horarios.update()
            self._ctrl_aula.update()
            self._ctrl_docente.update()

    # ── Edición: guardar cambios ──────────────────────────────

    def _guardar_edicion(self) -> None:
        """Guarda los cambios del horario en edición."""
        id_asig     = self._dd_unidad.value
        id_aula     = self._ctrl_aula.value
        id_doc      = self._ctrl_docente.value
        periodo_txt = (self._campo_periodo.value or "").strip()

        if not id_asig:
            self._msg("Selecciona una unidad de aprendizaje."); return
        if not id_aula or id_aula == _KEY_NUEVO:
            self._msg("Selecciona un aula."); return
        if not id_doc or id_doc == _KEY_NUEVO:
            self._msg("Selecciona un docente."); return
        if not periodo_txt:
            self._msg("Escribe el periodo."); return

        periodo_dto = self._service.crear_periodo(periodo_txt)
        if periodo_dto is None:
            self._msg("Error al registrar el periodo."); return

        fila = self._filas_horario[0]
        dia = (fila.dd_dia.value or "").strip()
        hi  = fila.hora_inicio.get_24h()
        hf  = fila.hora_fin.get_24h()

        if not dia:
            self._msg("Selecciona un día."); return

        try:
            t0    = datetime.strptime(hi, "%H:%M")
            t1    = datetime.strptime(hf, "%H:%M")
            delta = max(0, (t1 - t0).seconds) // 3600
        except ValueError:
            self._msg(f"Formato inválido: {hi} – {hf}"); return

        # ── Validación de tronco común (por semestre) ──────────
        id_materia = self._service.obtener_id_materia(int(id_asig))
        es_tronco  = id_materia is not None
        id_sem     = int(self._dd_semestre.value) if self._dd_semestre.value else None

        filas_edit = [{"dia": dia, "hora_inicio": hi, "hora_fin": hf}]
        error = self._validar_tronco(es_tronco, id_materia, id_sem, filas_edit)
        if error:
            self._msg(error); return

        ok, msg = self._service.actualizar_horario(
            id_horario=self._editando_id,
            dto=GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=dia, hora_inicio=hi, hora_fin=hf,
                total_horas=delta, id_plan=self._id_plan,
            ),
        )
        if not ok:
            self._msg(msg); return

        # Actualizar caché de tronco
        if es_tronco and id_materia is not None and id_sem is not None:
            self._registrar_tronco_cache(id_sem, id_materia, filas_edit)

        self._msg("¡Horario actualizado correctamente!")
        self._cancelar_edicion()
        self._recargar_tabla()

    # ── Tabla inferior ────────────────────────────────────────

    def _recargar_tabla(self) -> None:
        try:
            id_sem = self._dd_semestre.value
            if not id_sem:
                self._tabla.rows = []
                if self.page:
                    self._tabla.update()
                return
            registros = self._service.obtener_horarios_filtrados(
                id_plan=self._id_plan,
                id_lies=self._id_lies_activa,
                id_semestre=int(id_sem),
                id_semestre_opt=self._sem_opt.id if self._sem_opt else None,
            )
            self._tabla.rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(r.clave, size=12,
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
                            on_click=lambda _, rid=r.id_horario:
                                self._iniciar_edicion(rid),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=Colores.ROJO,
                            icon_size=16, tooltip="Eliminar",
                            on_click=lambda _, rid=r.id_horario:
                                self._confirmar_eliminar(rid),
                        ),
                    ], spacing=0)),
                ])
                for r in registros
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

    def _eliminar(self, id_horario: int) -> None:
        ok, msg = self._service.eliminar_horario(id_horario)
        self._msg(msg)
        if ok:
            self._recargar_tabla()

    # ── Helpers de PDF ─────────────────────────────────────────

    def _datos_para_pdf(self):
        """Retorna (registros, nombre_plan, lies_nombre, nombre_sem) o None."""
        id_sem = self._dd_semestre.value
        if not id_sem:
            self._msg("Selecciona un semestre antes de exportar.")
            return None
        registros = self._service.obtener_horarios_filtrados(
            id_plan=self._id_plan,
            id_lies=self._id_lies_activa,
            id_semestre=int(id_sem),
            id_semestre_opt=self._sem_opt.id if self._sem_opt else None,
        )
        if not registros:
            self._msg("No hay horarios registrados para exportar.")
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
        """Genera PDF temporal y muestra vista previa en un diálogo."""
        ruta = os.path.join(
            tempfile.gettempdir(),
            f"preview_{self._id_plan}_{self._id_lies_activa}.pdf",
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
                f"preview_{self._id_plan}_{self._id_lies_activa}.png",
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
        # Limpiar estado del formulario para que al volver quede vacío
        self._editando_id = None
        self._dd_semestre.value = None
        self._dd_unidad.options = []
        self._dd_unidad.value = None
        self._dd_unidad.disabled = True
        self._tipo_txt.value = ""
        self._ctrl_aula.value = None
        self._ctrl_docente.value = None
        self._campo_periodo.value = ""
        # Restaurar horario a una fila vacía
        while len(self._filas_horario) > 1:
            f = self._filas_horario.pop()
            self._col_horarios.controls.remove(f)
        fila = self._filas_horario[0]
        fila.dd_dia.value = None
        fila.hora_inicio.set_from_24h("01:00")
        fila.hora_fin.set_from_24h("01:00")
        self._actualizar_total(None)
        self._btn_accion.text = "+ Agregar"
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
