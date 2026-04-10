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
# Picker de hora con scroll (rueda del mouse)
# ─────────────────────────────────────────────────────────────
class _ScrollColumn(ft.GestureDetector):
    """Columna de valor que cambia con scroll del mouse."""

    def __init__(
        self,
        items: list[str],
        initial: int = 0,
        width: int = 36,
        on_change: Callable | None = None,
    ) -> None:
        self._items    = items
        self._selected = initial
        self._on_change = on_change

        self._txt = ft.Text(
            items[initial], size=14, weight=ft.FontWeight.W_700,
            color=_NEGRO, font_family=Fuentes.CAMPOS,
            text_align=ft.TextAlign.CENTER,
        )
        box = ft.Container(
            content=self._txt,
            width=width, height=30,
            alignment=ft.alignment.center,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=4,
            bgcolor=Colores.BLANCO,
        )
        super().__init__(content=box, on_scroll=self._on_scroll)

    def _on_scroll(self, e: ft.ScrollEvent) -> None:
        self._move(-1 if e.scroll_delta_y < 0 else 1)

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
        self._ruta_membrete = ruta_membrete

        # ── FilePicker para guardar PDF ────────────────────────
        self._save_picker = ft.FilePicker(on_result=self._on_save_result)
        page.overlay.append(self._save_picker)

        # ── Datos iniciales ───────────────────────────────────
        nombre_plan     = service.obtener_nombre_plan(id_plan)
        semestres_raw   = service.obtener_semestres(id_plan)
        self._sem_opt   = next((s for s in semestres_raw if s.numero == 0), None)
        self._semestres = [s for s in semestres_raw if s.numero > 0]
        self._all_lies  = service.obtener_todas_lies_del_plan(id_plan)
        self._aulas     = list(service.obtener_aulas())
        self._docentes  = list(service.obtener_docentes())
        self._tipos     = service.obtener_tipos_materia()
        self._unidades  = []
        self._id_lies_activa = self._all_lies[0].id if self._all_lies else 0

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
        # -- Unidad de aprendizaje: dropdown con búsqueda integrada --
        self._unidad_all_opts: list[ft.dropdown.Option] = []  # copia maestra
        self._buscando_unidad = False

        self._btn_buscar_unidad = ft.Container(
            content=ft.Icon(
                ft.Icons.SEARCH,
                color=Colores.AZUL_PRIMARIO,
                size=20,
            ),
            on_click=self._toggle_buscar_unidad,
            tooltip="Buscar unidad",
            ink=True,
            padding=ft.padding.all(4),
        )
        self._dd_unidad = ft.Dropdown(
            hint_text="Seleccionar unidad",
            options=[], disabled=True,
            on_change=self._on_unidad_cambiada,
            suffix=self._btn_buscar_unidad,
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
            ],
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

        btn_agregar = ft.ElevatedButton(
            text="+ Agregar",
            on_click=self._agregar,
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

        col3 = ft.Column(
            spacing=4,
            controls=[
                _lbl("Tipo"),
                tipo_contenedor,
                ft.Container(height=8),
                _lbl("Docente"),
                self._ctrl_docente,
                ft.Container(height=20),
                btn_agregar,
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
        for btn in self._lies_btns:
            activo = btn.text == lnombre
            btn.style.bgcolor = (Colores.AZUL_PRIMARIO if activo
                                 else "transparent")
            btn.style.color   = (Colores.BLANCO if activo
                                 else Colores.AZUL_PRIMARIO)
            if self.page:
                btn.update()
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

        if self.page:
            self._dd_unidad.update()
            self._tipo_txt.update()

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

    # ── Guardar horario ───────────────────────────────────────

    def _agregar(self, _) -> None:
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

        alguno_ok = False
        for fila in self._filas_horario:
            dia = (fila.dd_dia.value or "").strip()
            hi  = fila.hora_inicio.get_24h()
            hf  = fila.hora_fin.get_24h()
            if not dia:
                continue
            try:
                t0    = datetime.strptime(hi, "%H:%M")
                t1    = datetime.strptime(hf, "%H:%M")
                delta = max(0, (t1 - t0).seconds) // 3600
            except ValueError:
                self._msg(f"Formato inválido: {hi} – {hf}"); return

            ok, msg = self._service.guardar_horario(GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=dia, hora_inicio=hi, hora_fin=hf,
                total_horas=delta, id_plan=self._id_plan,
            ))
            if not ok:
                self._msg(msg); return
            alguno_ok = True

        if not alguno_ok:
            self._msg("Completa al menos un horario (día + horas)."); return
        self._msg("¡Horario agregado correctamente!")
        self._recargar_tabla()

    # ── Tabla inferior ────────────────────────────────────────

    def _recargar_tabla(self) -> None:
        registros = self._service.obtener_horarios(self._id_plan)
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
                            self._msg("Editar: próximamente"),
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
        """Retorna (registros, nombre_plan, lies_nombre) o None."""
        registros = self._service.obtener_horarios(self._id_plan)
        if not registros:
            self._msg("No hay horarios registrados para exportar.")
            return None
        nombre_plan = self._service.obtener_nombre_plan(self._id_plan)
        lies_nombre = ""
        for lies in self._all_lies:
            if lies.id == self._id_lies_activa:
                lies_nombre = lies.nombre
                break
        return registros, nombre_plan, lies_nombre

    def _generar_pdf(self, ruta: str) -> bool:
        """Genera el PDF en la ruta indicada. Retorna True si tuvo éxito."""
        datos = self._datos_para_pdf()
        if datos is None:
            return False
        registros, nombre_plan, lies_nombre = datos
        try:
            GeneradorPDF(
                horarios=registros,
                nombre_plan=nombre_plan,
                nombre_lies=lies_nombre,
                ruta_membrete=self._ruta_membrete,
                ruta_salida=ruta,
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
        if self._on_volver:
            self._on_volver()

    def _msg(self, texto: str) -> None:
        self._page.open(ft.SnackBar(content=ft.Text(texto)))
