"""
ui/views/horario_docente_view.py
Vista embebida para generar, previsualizar y exportar el horario
semanal de un docente en formato PDF.

Cambios:
  - Dropdown «Grado» como primer filtro (antes de Docente).
  - Cascada: Grado → Docente → Periodo → Plan de estudios → Semestre.
  - El membrete se obtiene automáticamente del plan de estudios
    seleccionado (gestor_membrete), igual que en crear_plan_view.
  - «Limpiar» regresa al estado inicial completo (hint_text visibles,
    dropdowns deshabilitados excepto Grado).
"""

import os
import tempfile
from typing import Callable

import flet as ft

from application.services.horario_service import HorarioService
from application.dto.horario_docente_dto import HorarioDocenteResumenDTO
from ui.components.plan_components import Colores, Fuentes
from ui.pdf.generador_pdf_docente import GeneradorPdfDocente

# ─────────────────────────────────────────────────────────────
# Constantes de layout
# ─────────────────────────────────────────────────────────────
_W_DD = 220
_W_BTN = 220
_COLOR_HDR = "#3D5FD2"
_NEGRO = "#000000"
_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]


# ─────────────────────────────────────────────────────────────
# Helpers de estilo
# ─────────────────────────────────────────────────────────────
def _opcion(key: str, text: str) -> ft.dropdown.Option:
    return ft.dropdown.Option(
        key=key, text=text,
        text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS),
    )


def _dd_kw(width: int) -> dict:
    return dict(
        border_color=Colores.BORDE,
        focused_border_color=Colores.AZUL_PRIMARIO,
        bgcolor=Colores.BLANCO,
        fill_color=Colores.BLANCO,
        color=_NEGRO,
        text_size=13,
        width=width,
        content_padding=ft.padding.symmetric(horizontal=10, vertical=8),
        text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS),
        hint_style=ft.TextStyle(color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
    )


def _lbl(texto: str) -> ft.Text:
    return ft.Text(
        texto, size=13, weight=ft.FontWeight.W_600,
        color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
    )


# ─────────────────────────────────────────────────────────────
# Cabecera de la vista
# ─────────────────────────────────────────────────────────────
class _CabeceraDocente(ft.Container):
    """Icono | «Horario docente» | X roja."""

    def __init__(self, on_cerrar: Callable) -> None:
        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PEOPLE_ALT_OUTLINED,
                            color=Colores.AZUL_PRIMARIO, size=36),
                    ft.Text(
                        "Horario docente",
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
            border=ft.border.only(bottom=ft.BorderSide(3, Colores.AZUL_PRIMARIO)),
        )


# ─────────────────────────────────────────────────────────────
# Vista principal: Horario por Docente
# ─────────────────────────────────────────────────────────────
class HorarioDocenteView(ft.Container):
    """Panel embebido dentro de PlanesView para la pestaña
    'Horario por docente'.

    Flujo:
    1. Seleccionar Grado → Docente → Periodo → Plan de estudios → Semestre
    2. Clic en «Generar» → consultar BD → previsualizar tabla
    3. «Ver Documento» → popup con imagen del PDF (membrete del plan + tabla)
    4. «Exportar» → guardar .pdf en ruta elegida
    5. «Limpiar» → resetear al estado inicial
    """

    def __init__(
        self,
        page: ft.Page,
        service: HorarioService,
        ruta_membrete: str | None = None,
    ) -> None:
        self._page = page
        self._service = service
        self._ruta_membrete: str | None = ruta_membrete

        # Estado interno
        self._resumen: HorarioDocenteResumenDTO | None = None

        # FilePicker para exportar
        self._save_picker = ft.FilePicker(on_result=self._on_save_result)

        # Datos iniciales
        self._docentes = list(service.obtener_docentes())
        self._niveles  = list(service.obtener_niveles_con_docente())

        # ════════ DROPDOWNS ════════

        # 1) Grado — siempre habilitado
        self._dd_grado = ft.Dropdown(
            hint_text="Seleccionar grado",
            options=[_opcion(str(n["id"]), n["nombre"]) for n in self._niveles],
            on_change=self._on_grado_cambiado,
            **_dd_kw(_W_DD),
        )

        # 2) Docente — depende de Grado
        self._dd_docente = ft.Dropdown(
            hint_text="Seleccionar docente",
            options=[],
            disabled=True,
            on_change=self._on_docente_cambiado,
            **_dd_kw(_W_DD),
        )

        # 3) Periodo — depende de Grado + Docente
        self._dd_periodo = ft.Dropdown(
            hint_text="Seleccionar periodo",
            options=[],
            disabled=True,
            on_change=self._on_periodo_cambiado,
            **_dd_kw(_W_DD),
        )

        # 4) Plan de estudios — depende de Grado + Docente + Periodo
        self._dd_plan = ft.Dropdown(
            hint_text="Seleccionar plan de estudios",
            options=[],
            disabled=True,
            on_change=self._on_plan_cambiado,
            **_dd_kw(_W_DD),
        )

        # 5) Semestre — depende de todos los anteriores
        self._dd_semestre = ft.Dropdown(
            hint_text="Seleccionar semestre",
            options=[],
            disabled=True,
            **_dd_kw(_W_DD),
        )

        # ════════ BOTONES ════════

        btn_limpiar = ft.OutlinedButton(
            text="Limpiar",
            width=_W_BTN,
            on_click=lambda _: self._limpiar(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=30, vertical=14),
                side=ft.BorderSide(2, Colores.AZUL_PRIMARIO),
                color=Colores.ROJO,
                text_style=ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
        )

        btn_generar = ft.ElevatedButton(
            text="Generar",
            width= _W_BTN,
            on_click=lambda _: self._generar(),
            bgcolor=Colores.AZUL_PRIMARIO,
            color=Colores.BLANCO,
            elevation=0,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=40, vertical=14),
                text_style=ft.TextStyle(
                    size=15, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
        )

        # ════════ FORMULARIO ════════

        formulario = ft.Container(
            alignment=ft.alignment.center,  # 👈 CLAVE: centra todo el bloque
            content=ft.Container(
                bgcolor=Colores.BLANCO,
                border=ft.border.all(1.5, Colores.BORDE),
                border_radius=8,
                padding=ft.padding.all(30),
                margin=ft.margin.symmetric(horizontal=20, vertical=10),
                content=ft.Container(
                    width=(_W_DD * 4) + (20 * 3),  # 👈 mantiene tu grid
                    content=ft.Column(
                        controls=[
                            # Fila 1
                            ft.Row(
                                controls=[
                                    ft.Column([_lbl("Grado"), self._dd_grado], spacing=4),
                                    ft.Column([_lbl("Docente"), self._dd_docente], spacing=4),
                                    ft.Column([_lbl("Periodo"), self._dd_periodo], spacing=4),
                                    ft.Container(content=btn_limpiar, margin=ft.margin.only(top=18)),
                                ],
                                spacing=20,
                                vertical_alignment=ft.CrossAxisAlignment.START,  # 👈 corregido
                            ),

                            ft.Container(height=8),

                            # Fila 2
                            ft.Row(
                                controls=[
                                    ft.Column([_lbl("Plan de estudios"), self._dd_plan], spacing=4),
                                    ft.Column([_lbl("Semestre"), self._dd_semestre], spacing=4),
                                    ft.Container(width=_W_DD),
                                    ft.Container(content=btn_generar, margin=ft.margin.only(top=18)),
                                ],
                                spacing=20,
                                vertical_alignment=ft.CrossAxisAlignment.START,  # 👈 corregido
                            ),
                        ],
                        spacing=0,
                    ),
                ),
            ),
        )

        # ════════ PREVISUALIZACIÓN ════════

        self._lbl_prev = ft.Text(
            "Previsualización",
            size=14, weight=ft.FontWeight.W_600,
            color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
            visible=False,
        )

        self._tabla_prev = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(
                    c, size=11, weight=ft.FontWeight.W_600,
                    font_family=Fuentes.CAMPOS, color=Colores.BLANCO))
                for c in ["Hora"] + _DIAS
            ],
            rows=[],
            heading_row_color=Colores.AZUL_PRIMARIO,
            heading_row_height=36,
            data_row_max_height=56,
            column_spacing=8,
            horizontal_margin=8,
            border=ft.border.all(1, _NEGRO),
            border_radius=0,
            visible=False,
            expand=True,
        )

        # ════════ BOTONES INFERIORES ════════

        self._btn_ver = ft.ElevatedButton(
            text="Ver Documento",
            on_click=lambda _: self._ver_documento(),
            bgcolor=Colores.AZUL_PRIMARIO,
            color=Colores.BLANCO,
            elevation=0,
            visible=False,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=30, vertical=12),
                text_style=ft.TextStyle(
                    size=14, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
        )

        self._btn_exportar = ft.ElevatedButton(
            text="Exportar",
            on_click=lambda _: self._exportar(),
            bgcolor=Colores.AZUL_PRIMARIO,
            color=Colores.BLANCO,
            elevation=0,
            visible=False,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=40, vertical=12),
                text_style=ft.TextStyle(
                    size=14, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
        )

        fila_botones = ft.Row(
            controls=[self._btn_ver, self._btn_exportar],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # ════════ PANEL PREVIO ════════

        panel_prev = ft.Container(
            bgcolor=Colores.BLANCO,
            border=ft.border.all(1.5, Colores.BORDE),
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=20, vertical=5),
            padding=ft.padding.all(20),
            content=ft.Column(
                controls=[
                    self._lbl_prev,
                    ft.Container(height=8),
                    ft.Row(controls=[self._tabla_prev], scroll=ft.ScrollMode.AUTO),
                    ft.Container(height=14),
                    fila_botones,
                ],
                spacing=0,
            ),
            visible=False,
        )
        self._panel_prev = panel_prev

        # ════════ ENSAMBLADO ════════

        contenido = ft.Column(
            controls=[
                formulario,
                ft.Divider(height=1, color=Colores.BORDE),
                panel_prev,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        super().__init__(
            content=contenido,
            expand=True,
            bgcolor=Colores.BLANCO,
        )

    # ── Ciclo de vida ─────────────────────────────────────────

    def did_mount(self) -> None:
        if self._save_picker not in self._page.overlay:
            self._page.overlay.append(self._save_picker)
            self._page.update()

    def will_unmount(self) -> None:
        if self._save_picker in self._page.overlay:
            self._page.overlay.remove(self._save_picker)
            self._page.update()

    # ── Cascada: Grado → Docente → Periodo → Plan → Semestre ──

    def _on_grado_cambiado(self, _) -> None:
        """Al seleccionar grado carga los docentes con horarios en ese grado."""
        id_nivel = self._dd_grado.value

        for dd in (self._dd_docente, self._dd_periodo, self._dd_plan, self._dd_semestre):
            dd.value = None
            dd.options = []
            dd.disabled = True

        if id_nivel:
            docentes_nivel = [
                d for d in self._docentes
                if len(self._service.obtener_periodos_por_docente_nivel(
                    d.id, int(id_nivel))) > 0
            ]
            self._dd_docente.options = [
                _opcion(str(d.id), d.nombre) for d in docentes_nivel
            ]
            self._dd_docente.disabled = (len(docentes_nivel) == 0)

        if self.page:
            for dd in (self._dd_docente, self._dd_periodo, self._dd_plan, self._dd_semestre):
                dd.update()

    def _on_docente_cambiado(self, _) -> None:
        """Carga periodos del docente filtrados por grado seleccionado."""
        id_nivel = self._dd_grado.value
        id_doc   = self._dd_docente.value

        for dd in (self._dd_periodo, self._dd_plan, self._dd_semestre):
            dd.value = None
            dd.options = []
            dd.disabled = True

        if id_doc and id_nivel:
            periodos = self._service.obtener_periodos_por_docente_nivel(
                int(id_doc), int(id_nivel))
            self._dd_periodo.options = [_opcion(str(p.id), p.nombre) for p in periodos]
            self._dd_periodo.disabled = (len(periodos) == 0)

        if self.page:
            for dd in (self._dd_periodo, self._dd_plan, self._dd_semestre):
                dd.update()

    def _on_periodo_cambiado(self, _) -> None:
        """Carga planes del grado+docente+periodo seleccionados."""
        id_nivel = self._dd_grado.value
        id_doc   = self._dd_docente.value
        id_per   = self._dd_periodo.value

        for dd in (self._dd_plan, self._dd_semestre):
            dd.value = None
            dd.options = []
            dd.disabled = True

        if id_doc and id_per and id_nivel:
            planes = self._service.obtener_planes_por_docente_nivel_periodo(
                int(id_doc), int(id_nivel), int(id_per))
            self._dd_plan.options = [_opcion(str(p.id), p.nombre) for p in planes]
            self._dd_plan.disabled = (len(planes) == 0)

        if self.page:
            for dd in (self._dd_plan, self._dd_semestre):
                dd.update()

    def _on_plan_cambiado(self, _) -> None:
        """Carga semestres y obtiene el membrete del plan seleccionado."""
        id_doc  = self._dd_docente.value
        id_per  = self._dd_periodo.value
        id_plan = self._dd_plan.value

        self._dd_semestre.value = None
        self._dd_semestre.options = []
        self._dd_semestre.disabled = True

        if id_doc and id_per and id_plan:
            sems = self._service.obtener_semestres_por_docente_plan_periodo(
                int(id_doc), int(id_plan), int(id_per))
            self._dd_semestre.options = [
                _opcion(str(s.id), f"Semestre {s.numero}") for s in sems
            ]
            self._dd_semestre.disabled = (len(sems) == 0)

            # Membrete del plan seleccionado
            self._ruta_membrete = self._service.obtener_ruta_membrete(int(id_plan))

        if self.page:
            self._dd_semestre.update()

    # ── Generar ───────────────────────────────────────────────

    def _generar(self) -> None:
        id_nivel = self._dd_grado.value
        id_doc   = self._dd_docente.value
        id_per   = self._dd_periodo.value
        id_plan  = self._dd_plan.value
        id_sem   = self._dd_semestre.value

        if not id_nivel:
            self._msg("Selecciona un grado."); return
        if not id_doc:
            self._msg("Selecciona un docente."); return
        if not id_per:
            self._msg("Selecciona un periodo."); return
        if not id_plan:
            self._msg("Selecciona un plan de estudios."); return
        if not id_sem:
            self._msg("Selecciona un semestre."); return
        if not self._ruta_membrete:
            self._msg("El plan seleccionado no tiene membrete. "
                      "Asígnale uno desde 'Crear plan de estudios'."); return

        resumen = self._service.obtener_horarios_docente(
            id_docente=int(id_doc),
            id_plan=int(id_plan),
            id_periodo=int(id_per),
            id_semestre=int(id_sem),
        )

        if not resumen.filas:
            self._msg("No se encontraron horarios para el docente "
                      "con los filtros seleccionados.")
            return

        self._resumen = resumen
        self._construir_preview()
        self._msg("¡Horario generado correctamente!")

    def _construir_preview(self) -> None:
        if not self._resumen:
            return

        filas = self._resumen.filas
        franjas = sorted(set(
            (f.hora_inicio, f.hora_fin) for f in filas
            if f.hora_inicio and f.hora_fin
        ))
        mapa: dict[tuple, str] = {}
        for f in filas:
            if f.dia and f.hora_inicio:
                mapa[(f.dia, f.hora_inicio)] = f.nombre_materia

        rows = []
        for (hi, hf) in franjas:
            hora_txt = f"{hi} - {hf}"
            cells = [
                ft.DataCell(ft.Text(hora_txt, size=11,
                                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                                    weight=ft.FontWeight.W_600)),
            ]
            for dia in _DIAS:
                materia = mapa.get((dia, hi), "")
                cell_content = ft.Container(
                    content=ft.Text(materia, size=10,
                                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO),
                    bgcolor="#B5CBF7" if materia else None,
                    padding=ft.padding.all(4),
                    border_radius=2,
                    width=120,
                )
                cells.append(ft.DataCell(cell_content))
            rows.append(ft.DataRow(cells=cells))

        self._tabla_prev.rows = rows
        self._tabla_prev.visible = True
        self._lbl_prev.visible = True
        self._btn_ver.visible = True
        self._btn_exportar.visible = True
        self._panel_prev.visible = True

        if self.page:
            self._tabla_prev.update()
            self._lbl_prev.update()
            self._btn_ver.update()
            self._btn_exportar.update()
            self._panel_prev.update()

    # ── Ver Documento (popup) ─────────────────────────────────

    def _ver_documento(self) -> None:
        if not self._resumen:
            self._msg("Primero genera el horario.")
            return

        ruta_pdf = os.path.join(tempfile.gettempdir(),
                                 f"preview_docente_{id(self)}.pdf")
        try:
            GeneradorPdfDocente(
                resumen=self._resumen,
                ruta_membrete=self._ruta_membrete,
                ruta_salida=ruta_pdf,
            ).generar()
        except Exception as e:
            self._msg(f"Error al generar vista previa: {e}")
            return

        try:
            import fitz
            doc_pdf = fitz.open(ruta_pdf)
            page_pdf = doc_pdf[0]
            pix = page_pdf.get_pixmap(dpi=150)
            img_path = ruta_pdf.replace(".pdf", ".png")
            pix.save(img_path)
            doc_pdf.close()

            dlg = ft.AlertDialog(
                modal=True,
                bgcolor=Colores.BLANCO,
                title=ft.Text("Vista previa - Horario Docente",
                               font_family=Fuentes.TITULO, size=18,
                               color=Colores.AZUL_PRIMARIO),
                content=ft.Container(
                    content=ft.Column(
                        controls=[ft.Image(src=img_path, fit=ft.ImageFit.CONTAIN, width=550)],
                        scroll=ft.ScrollMode.AUTO,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=600, height=550,
                    border=ft.border.all(1, Colores.AZUL_PRIMARIO),
                    border_radius=8,
                ),
                actions=[ft.TextButton("Cerrar", on_click=lambda _: self._page.close(dlg))],
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(radius=10),
            )
            self._page.open(dlg)
        except ImportError:
            self._msg("PyMuPDF (fitz) no está instalado para vista previa.")
        except Exception as e:
            self._msg(f"Error al mostrar vista previa: {e}")

    # ── Exportar ──────────────────────────────────────────────

    def _exportar(self) -> None:
        if not self._resumen:
            self._msg("Primero genera el horario.")
            return
        nombre_doc = self._resumen.nombre_docente.replace(" ", "_")
        self._save_picker.save_file(
            dialog_title="Guardar horario docente",
            file_name=f"horario_{nombre_doc}.pdf",
            allowed_extensions=["pdf"],
        )

    def _on_save_result(self, e: ft.FilePickerResultEvent) -> None:
        if not e.path or not self._resumen:
            return
        ruta = e.path
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"
        try:
            GeneradorPdfDocente(
                resumen=self._resumen,
                ruta_membrete=self._ruta_membrete,
                ruta_salida=ruta,
            ).generar()
            self._msg(f"Documento guardado en: {ruta}")
        except Exception as ex:
            self._msg(f"Error al exportar: {ex}")

    # ── Limpiar — estado inicial completo ─────────────────────

    def _limpiar(self) -> None:
        """Regresa al estado inicial: Grado con sus opciones, el resto
        deshabilitado y con hint_text (options vacío)."""
        # Refrescar niveles por si cambiaron
        self._niveles = list(self._service.obtener_niveles_con_docente())

        self._dd_grado.value = None
        self._dd_grado.options = [
            _opcion(str(n["id"]), n["nombre"]) for n in self._niveles
        ]

        for dd in (self._dd_docente, self._dd_periodo, self._dd_plan, self._dd_semestre):
            dd.value = None
            dd.options = []
            dd.disabled = True

        # Limpiar membrete y resultado
        self._ruta_membrete = None
        self._resumen = None

        # Ocultar panel de previsualización
        self._tabla_prev.rows = []
        self._tabla_prev.visible = False
        self._lbl_prev.visible = False
        self._btn_ver.visible = False
        self._btn_exportar.visible = False
        self._panel_prev.visible = False

        if self.page:
            for dd in (self._dd_grado, self._dd_docente, self._dd_periodo,
                       self._dd_plan, self._dd_semestre):
                dd.update()
            self._tabla_prev.update()
            self._lbl_prev.update()
            self._btn_ver.update()
            self._btn_exportar.update()
            self._panel_prev.update()

    # ── Mensajes ──────────────────────────────────────────────

    def _msg(self, texto: str) -> None:
        print(f"[HorarioDocenteView] {texto}")
        self._page.open(ft.SnackBar(content=ft.Text(texto)))