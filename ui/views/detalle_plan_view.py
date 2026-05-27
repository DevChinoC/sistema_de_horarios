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
from application.state.detalle_plan_state import DetallePlanState
from application.controllers.detalle_plan_controller import DetallePlanController

from ui.utils.reset_utils import reset_dropdown
from ui.components.time_picker import ScrollTimePicker
from ui.components.fila_horario import FilaHorario as _FilaHorario
from ui.components.dropdown_con_nuevo import DropdownConNuevo as _DropdownConNuevo
from ui.components.buscador_unidad import BuscadorUnidad as _BuscadorUnidad
from application.mappers.horario_mapper import HorarioMapper
from application.mappers.opciones_mapper import OpcionesMapper
from application.presenters.detalle_plan_presenter import DetallePlanPresenter
from ui.builders.horario_row_builder import HorarioRowBuilder

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
        self._tipos     = service.obtener_tipos_materia()

        # MIIDT: tiene LIES → inicializar con la primera (tabs visibles)
        # DIIDT/otros: sin LIES → id_lies_activa = None (sin tabs, sin filtro)
        self._todas_lies = list(self._all_lies)
        _id_lies_init = self._all_lies[0].id if self._all_lies else None
        self._id_lies_activa = _id_lies_init

        # ── Estado centralizado (sesión, cachés, catálogos) ───
        self._state = DetallePlanState(
            service=service,
            id_plan=id_plan,
            id_lies_activa=_id_lies_init,  # None para DIIDT/otros
            sem_opt_id=self._sem_opt.id if self._sem_opt else None,
        )

        # ── Flags de blindaje contra eventos automáticos de Flet ──
        self._suspendiendo_eventos = False
        self._modo_edicion = False
        self._semestre_filtro_actual = None  # filtro real para tabla/PDF

        # Poblar catálogos en el State
        self._state.aulas    = list(service.obtener_aulas())
        self._state.docentes = list(service.obtener_docentes())
        self._state.unidades = []

        # Aliases de vista — apuntan al state (no copias independientes)
        self._aulas    = self._state.aulas
        self._docentes = self._state.docentes
        self._unidades = self._state.unidades

        # ── Controller (coordina sin renderizar) ──────────────
        self._ctrl = DetallePlanController(
            service=service,
            state=self._state,
            id_plan=id_plan,
        )
        # ── Presenter (diálogos, mensajes) ────────────────────
        self._presenter = DetallePlanPresenter(page)


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
        """Precarga horarios de un plan_generado seleccionando el semestre
        adecuado y recargando la tabla desde BD."""
        registros = self._service.obtener_horarios_de_plan_generado(id_plan_generado)
        if not registros:
            return
        # Auto-seleccionar el primer semestre que tenga horarios
        if self._semestres and not self._dd_semestre.value:
            sems_con_datos = {r.numero_semestre for r in registros if r.numero_semestre > 0}
            sem_target = None
            for s in self._semestres:
                if s.numero in sems_con_datos:
                    sem_target = s
                    break
            if sem_target is None:
                sem_target = self._semestres[0]
            self._dd_semestre.value = str(sem_target.id)
            self._semestre_filtro_actual = str(sem_target.id)
            if self.page:
                self._dd_semestre.update()
            self._on_semestre_cambiado(None)
        # Recargar tabla desde BD
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
        # Recargar tabla desde BD al cambiar de LIES
        if self._dd_semestre.value:
            self._on_semestre_cambiado(None)
        else:
            self._tabla.rows = []
            if self.page:
                self._tabla.update()

    # ── Semestre → cargar unidades ────────────────────────────

    def _on_semestre_cambiado(self, _) -> None:
        # ── Blindaje: ignorar eventos automáticos de Flet ─────
        if self._suspendiendo_eventos:
            return

        id_sem = self._dd_semestre.value
        if not id_sem:
            return

        # Persistir el filtro visual (NO se toca durante edición)
        self._semestre_filtro_actual = id_sem

        # ── Lógica delegada al controller ─────────────────────
        unidades = self._ctrl.cambiar_semestre(
            id_sem=int(id_sem),
            id_lies=self._id_lies_activa,
            sem_opt_id=self._sem_opt.id if self._sem_opt else None,
        )
        self._unidades = unidades  # alias local para widgets que lo leen

        # ── Solo UI: actualizar widgets ───────────────────────
        opts = [_opcion(str(u.id_asignacion), u.nombre) for u in unidades]
        self._unidad_all_opts = list(opts)
        self._dd_unidad.options  = opts
        self._dd_unidad.value    = None
        self._dd_unidad.disabled = not unidades
        self._tipo_txt.value     = ""

        self._buscador_unidad.set_opciones([
            (str(u.id_asignacion), u.nombre) for u in unidades
        ])

        if self._buscando_unidad:
            self._buscando_unidad = False
            self._buscador_unidad.desactivar()
            self._dd_unidad.visible = True
            self._btn_buscar_unidad.visible = True

        # ── Recargar tabla desde BD (fuente única de verdad) ───
        if not self._modo_edicion:
            self._recargar_tabla()

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

        id_sem = int(self._dd_semestre.value) if self._dd_semestre.value else None

        # ── Recopilar filas válidas ────────────────────────────
        filas_validas = self._recopilar_filas_validas()
        if filas_validas is None:
            return

        # ── Guardar cada fila — el service valida contra BD real ──
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

        self._msg("¡Horario agregado correctamente!")
        self._recargar_tabla()
        self._limpiar_formulario()


    # ── Edición: iniciar ──────────────────────────────────────

    def _iniciar_edicion(self, id_detalle: int) -> None:
        """Carga los datos del detalle en los campos del formulario.
        Usa flags de blindaje para evitar que Flet destruya estado."""
        detalle = self._service.obtener_detalle_por_id(id_detalle)
        if detalle is None:
            self._msg("No se encontró el horario."); return

        self._state.editando_id_detalle = id_detalle
        self._modo_edicion = True
        self._suspendiendo_eventos = True

        # 1. Semestre — poblar formulario SIN alterar el filtro.
        #    _suspendiendo_eventos=True bloquea _on_semestre_cambiado,
        #    por lo que _semestre_filtro_actual NO cambia aqui.
        self._dd_semestre.value = str(detalle.id_semestre)
        if self.page:
            self._dd_semestre.update()
        # Cargar unidades sin borrar la tabla
        self._cargar_unidades_sin_limpiar(str(detalle.id_semestre))

        # 2. Unidad de aprendizaje
        self._dd_unidad.value = str(detalle.id_asignacion)
        if self.page:
            self._dd_unidad.update()

        # Reactivar eventos ANTES de callbacks que los necesiten
        self._suspendiendo_eventos = False

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

        # 6. Horario (día + horas) – usar una sola fila (el detalle editado)
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
        """Restaura el formulario al modo agregar.
        Delega a _finalizar_edicion para evitar duplicar logica."""
        self._finalizar_edicion()

    def _guardar_edicion(self) -> None:
        """Guarda los cambios del detalle en edición.
        Actualiza SOLO el detalle específico (id_detalle_horario).
        Luego recarga TODO el estado visual desde BD."""
        campos = self._validar_campos_formulario()
        if campos is None:
            return
        id_asig, id_aula, id_doc, periodo_txt = campos

        periodo_dto = self._service.crear_periodo(periodo_txt)
        if periodo_dto is None:
            self._msg("Error al registrar el periodo."); return

        # ── Recopilar la fila del formulario ────────────────────
        filas_validas = self._recopilar_filas_validas()
        if filas_validas is None:
            return

        id_sem = int(self._dd_semestre.value) if self._dd_semestre.value else None

        # ── Actualizar SOLO el detalle específico en BD ──────────
        f0 = filas_validas[0]
        ok, msg = self._service.actualizar_detalle(
            id_detalle=self._state.editando_id_detalle,
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
            # Salir de modo edición incluso si falla
            self._finalizar_edicion()
            return

        self._msg("¡Horario actualizado correctamente!")
        # ── Recarga transaccional: BD → tabla + preview + totales ──
        self._finalizar_edicion()

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

    # ── (cachés eliminados — la BD es la fuente de verdad) ────

    # ── Fuente única de verdad: BD ─────────────────────────────

    def _obtener_registros_visibles(self):
        """Fuente única de verdad para tabla, preview y PDF.
        Consulta BD directamente — NO depende de ids_sesion."""
        id_sem = self._semestre_filtro_actual
        if not id_sem:
            return []
        return self._service.obtener_horarios_filtrados(
            id_plan=self._id_plan,
            id_lies=self._id_lies_activa,
            id_semestre=int(id_sem),
            id_semestre_opt=self._sem_opt.id if self._sem_opt else None,
        )

    # ── Tabla inferior ────────────────────────────────────────

    def _recargar_tabla(self) -> None:
        """Recarga la tabla desde BD — fuente única de verdad.
        Nunca depende de estado en memoria."""
        try:
            registros = self._obtener_registros_visibles()
            # Validación: siempre debe ser una lista
            if not isinstance(registros, list):
                registros = list(registros) if registros else []
            print(f"[_recargar_tabla] filtro={self._semestre_filtro_actual}, {len(registros)} registros desde BD")
            self._tabla.rows = HorarioRowBuilder.build_many(
                registros,
                on_editar=self._on_editar_click,
                on_eliminar=self._on_eliminar_click,
            )
            if self.page:
                self._tabla.update()
        except Exception as ex:
            self._msg(f"Error al recargar tabla: {ex}")

    def _finalizar_edicion(self) -> None:
        """Limpia el estado de edición y recarga TODO el estado visual.

        Flujo transaccional:
            1. Limpiar estado de edición
            2. Restaurar formulario al modo agregar
            3. Recargar tabla completa desde BD
        """
        # Blindar contra eventos asíncronos de Flet
        self._suspendiendo_eventos = True

        # 1. Limpiar estado de edición
        self._state.editando_id_detalle = None
        self._modo_edicion = False

        # 2. Restaurar dropdown al semestre-filtro original
        if self._semestre_filtro_actual:
            self._dd_semestre.value = self._semestre_filtro_actual
            if self.page:
                self._dd_semestre.update()

        # 3. Restaurar botones al modo agregar
        self._btn_accion.visible = True
        self._btn_guardar.visible = False
        self._btn_cancelar.visible = False

        # 4. Limpiar formulario (NO el semestre, para conservar la tabla)
        self._post_agregar_cleanup()

        # 5. Recargar tabla COMPLETA desde BD (usa _semestre_filtro_actual)
        self._recargar_tabla()

        # 6. Reactivar eventos
        self._suspendiendo_eventos = False

    def _confirmar_eliminar(self, id_horario: int) -> None:
        """Delegado al presenter."""
        self._presenter.confirmar_eliminar(
            on_confirmar=lambda: self._eliminar(id_horario)
        )

    def _on_editar_click(self, id_detalle: int, _=None) -> None:
        """Wrapper para functools.partial en tabla — recibe id_detalle_horario."""
        self._iniciar_edicion(id_detalle)

    def _on_eliminar_click(self, id_horario: int, _=None) -> None:
        """Wrapper para functools.partial en tabla."""
        self._confirmar_eliminar(id_horario)

    def _eliminar(self, id_horario: int) -> None:
        ok, msg = self._service.eliminar_horario(id_horario)
        self._msg(msg)
        if ok:
            self._recargar_tabla()

    # ── Helpers de PDF ─────────────────────────────────────────

    def _datos_para_pdf(self):
        """Retorna (registros, nombre_plan, lies_nombre, nombre_sem) o None.
        Usa BD como fuente única de verdad.
        """
        id_sem = self._semestre_filtro_actual
        if not id_sem:
            self._msg("Selecciona un semestre antes de exportar.")
            return None
        # Consultar BD directamente — sin filtrar por ids_sesion
        registros = self._obtener_registros_visibles()
        if not registros:
            self._msg("No hay horarios para exportar. "
                      "Agrega al menos un horario primero.")
            return None
        nombre_plan = self._service.obtener_nombre_plan(self._id_plan)
        lies_nombre = ""
        # Buscar en todas las LIES (no solo MIIDT) para PDF
        for lies in (self._all_lies or self._todas_lies):
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
        """Genera PDF temporal y muestra vista previa. Delegado al presenter."""
        import time as _time
        _ts = int(_time.time())
        ruta = os.path.join(
            tempfile.gettempdir(),
            f"preview_{self._id_plan}_{self._id_lies_activa}_{_ts}.pdf",
        )
        if not self._generar_pdf(ruta):
            return
        self._presenter.mostrar_preview_pdf(ruta)

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
        self._semestre_filtro_actual = None

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
        """Delegado al presenter."""
        self._presenter.mensaje(texto)