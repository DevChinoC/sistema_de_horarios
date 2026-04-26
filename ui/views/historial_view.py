"""
ui/views/historial_view.py
Vista embebida para la pestaña «Historial» dentro de PlanesView.

Muestra una tabla general de todos los horarios guardados (plan_generado),
agrupados por semestre/periodo. Permite:
  - Ver  → popup de previsualización del PDF con membrete
  - Editar → navega a DetallePlanView del plan correspondiente
  - Eliminar → diálogo de confirmación + borrado en cascada
"""

import os
import shutil
import tempfile
from typing import Callable

import flet as ft

from application.services.horario_service import HorarioService
from ui.components.plan_components import Colores, Fuentes, DialogoConfirmacion

# ─────────────────────────────────────────────────────────────
# Helpers de estilo
# ─────────────────────────────────────────────────────────────
_NEGRO = "#000000"
ANCHO_BTN = 170

def _lbl(texto: str) -> ft.Text:
    return ft.Text(
        texto, size=13, weight=ft.FontWeight.W_600,
        color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
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
        hint_style=ft.TextStyle(
            color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
    )

def _opcion(key: str, text: str) -> ft.dropdown.Option:
    return ft.dropdown.Option(
        key=key, text=text,
        text_style=ft.TextStyle(color=_NEGRO, font_family=Fuentes.CAMPOS),
    )


# ─────────────────────────────────────────────────────────────
# Vista principal de Historial
# ─────────────────────────────────────────────────────────────
class HistorialView(ft.Container):
    """Panel embebido en PlanesView para la pestaña «Historial».

    Muestra el historial general de planes generados por semestre.
    Acciones por fila: Ver (popup PDF), Editar (DetallePlanView), Eliminar.
    """

    def __init__(
        self,
        page: ft.Page,
        service: HorarioService,
        on_editar_plan: Callable[[int], None],
        ruta_membrete: str | None = None,
    ) -> None:
        self._page           = page
        self._service        = service
        self._on_editar_plan = on_editar_plan
        self._ruta_membrete  = ruta_membrete

        # ── FilePicker para exportar PDF ──────────────────────
        self._save_picker = ft.FilePicker(on_result=self._on_save_result)

        # Datos completos del historial
        self._todos: list = []
        self._filtrado: list = []          # resultado del último filtro
        self._selected_item = None         # item seleccionado de la tabla

        # ════════════════════ FILTROS ═════════════════════════

        self._dd_grado = ft.Dropdown(
            hint_text="Seleccionar grado",
            options=[],
            on_change=self._on_filtro_cambiado,
            **_dd_kw(200),
        )

        self._dd_plan = ft.Dropdown(
            hint_text="Seleccionar plan de estudios",
            options=[],
            on_change=self._on_filtro_cambiado,
            **_dd_kw(220),
        )

        self._dd_periodo = ft.Dropdown(
            hint_text="Seleccionar periodo",
            options=[],
            on_change=self._on_filtro_cambiado,
            **_dd_kw(180),
        )

        self._dd_semestre = ft.Dropdown(
            hint_text="Seleccionar semestre",
            options=[
                _opcion("1", "Semestre 1"),
                _opcion("2", "Semestre 2"),
                _opcion("3", "Semestre 3"),
                _opcion("4", "Semestre 4"),
                _opcion("5", "Semestre 5"),
                _opcion("6", "Semestre 6"),
                _opcion("7", "Semestre 7"),
                _opcion("8", "Semestre 8"),
                _opcion("9", "Semestre 9"),
                _opcion("10", "Semestre 10"),
            ],
            on_change=self._on_filtro_cambiado,
            **_dd_kw(180),
        )

        btn_buscar = ft.ElevatedButton(
            text="Buscar",
            width=ANCHO_BTN,
            on_click=lambda _: self._aplicar_filtros(),
            bgcolor=Colores.AZUL_PRIMARIO,
            color=Colores.BLANCO,
            elevation=0,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=30, vertical=14),
                text_style=ft.TextStyle(
                    size=14, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES),
            ),
        )

        btn_limpiar = ft.OutlinedButton(
            text="Limpiar filtros",
            width=ANCHO_BTN,
            on_click=lambda _: self._limpiar_filtros(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=30, vertical=14),
                side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                
                text_style=ft.TextStyle(
                    size=14, 
                    font_family=Fuentes.BOTONES,
                    weight=ft.FontWeight.BOLD,
                    color=Colores.ROJO,
                ),
             color=Colores.ROJO,
            ),
        
        )

        # ── Panel de filtros ──────────────────────────────────
        panel_filtros = ft.Container(
            bgcolor=Colores.BLANCO,
            border=ft.border.all(1.5, Colores.BORDE),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=24, vertical=40),

            margin=ft.margin.symmetric(horizontal=20, vertical=10),
            content=ft.Row(
                controls=[
                    # Dropdowns: Grado | Plan de estudios | Periodo | Semestre
                    ft.Column([_lbl("Grados"), self._dd_grado], spacing=3),
                    ft.Column([_lbl("Plan de estudios"), self._dd_plan], spacing=3),
                    ft.Column([_lbl("Periodo"), self._dd_periodo], spacing=3),
                    ft.Column([_lbl("Semestre"), self._dd_semestre], spacing=3),
                    # Botones apilados verticalmente a la derecha
                    ft.Column(
                        controls=[btn_buscar, btn_limpiar],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
        )

        # ════════════════════ TABLA ═══════════════════════════
        self._tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(
                    c, size=11, weight=ft.FontWeight.W_600,
                    font_family=Fuentes.CAMPOS, color=Colores.BLANCO))
                for c in ["Clave", "Grado", "Planes de estudios",
                           "Periodo", "Semestre", "Acción"]
            ],
            rows=[],
            heading_row_color=Colores.AZUL_PRIMARIO,
            heading_row_height=45,
            data_row_max_height=48,
            column_spacing=12,
            horizontal_margin=10,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=6,
            expand=True,
        )

        self._lbl_seleccion = ft.Text(
            "Selecciona una fila para exportar",
            size=12, italic=True,
            color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS,
        )

        self._btn_exportar = ft.ElevatedButton(
            text="Exportar",
            icon=ft.Icons.DOWNLOAD,
            bgcolor=Colores.AZUL_PRIMARIO,
            color=Colores.BLANCO,
            elevation=0,
            disabled=True,
            on_click=lambda _: self._exportar(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(
                    horizontal=30, vertical=10),
                text_style=ft.TextStyle(
                    size=13, font_family=Fuentes.BOTONES),
            ),
        )

        self._panel_tabla = ft.Container(
            bgcolor=Colores.BLANCO,
            border=ft.border.all(1.5, Colores.BORDE),
            border_radius=8,
            margin=ft.margin.symmetric(horizontal=20, vertical=5),
            padding=ft.padding.all(14),
            expand=True,
            visible=False,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self._tabla],
                        expand=True,
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[self._lbl_seleccion, self._btn_exportar],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
            ),
        )

        # ════════════════════ ENSAMBLADO ══════════════════════
        contenido = ft.Column(
            controls=[
                panel_filtros,
                self._panel_tabla,
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
        """Cargar datos al montar la vista (solo filtros, tabla oculta)."""
        # Agregar FilePicker al overlay de la página
        if self._save_picker not in self._page.overlay:
            self._page.overlay.append(self._save_picker)
            self._page.update()
        self._cargar_datos()

    def _cargar_datos(self) -> None:
        """Carga el historial completo desde la BD y puebla los filtros.
        NO renderiza la tabla — el usuario debe hacer clic en «Buscar»."""
        self._todos = self._service.obtener_historial_planes()
        self._poblar_filtros()

    def _poblar_filtros(self) -> None:
        """Llena los dropdowns de filtro con valores únicos del historial."""
        grados_vistos:  set[str] = set()
        planes_vistos:  set[str] = set()
        periodos_vistos: set[str] = set()

        opts_grado:   list[ft.dropdown.Option] = []
        opts_plan:    list[ft.dropdown.Option] = []
        opts_periodo: list[ft.dropdown.Option] = []

        for item in self._todos:
            if item.nombre_nivel not in grados_vistos:
                grados_vistos.add(item.nombre_nivel)
                opts_grado.append(_opcion(item.nombre_nivel, item.nombre_nivel))
            if item.nombre_plan not in planes_vistos:
                planes_vistos.add(item.nombre_plan)
                opts_plan.append(_opcion(item.nombre_plan, item.nombre_plan))
            if item.nombre_periodo not in periodos_vistos:
                periodos_vistos.add(item.nombre_periodo)
                opts_periodo.append(_opcion(item.nombre_periodo, item.nombre_periodo))

        self._dd_grado.options   = opts_grado
        self._dd_plan.options    = opts_plan
        self._dd_periodo.options = opts_periodo

        if self.page:
            self._dd_grado.update()
            self._dd_plan.update()
            self._dd_periodo.update()

    def _renderizar_tabla(self, items: list) -> None:
        """Construye las filas de la tabla con los items dados."""
        self._filtrado = items
        self._selected_item = None

        self._tabla.rows = [
            ft.DataRow(
                cells=[
                    # Clave
                    ft.DataCell(ft.Text(
                        item.clave, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    # Grado
                    ft.DataCell(ft.Text(
                        item.nombre_nivel, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    # Plan de estudios
                    ft.DataCell(ft.Text(
                        item.nombre_plan, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    # Periodo
                    ft.DataCell(ft.Text(
                        item.nombre_periodo, size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    # Semestre
                    ft.DataCell(ft.Text(
                        "Semestre 1", size=12,
                        font_family=Fuentes.CAMPOS, color=Colores.TEXTO)),
                    # Acciones
                    ft.DataCell(ft.Row(
                        controls=[
                            # Ver — popup con previsualización PDF
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY_OUTLINED,
                                icon_color=Colores.AZUL_PRIMARIO,
                                icon_size=18,
                                tooltip="Ver horario",
                                on_click=lambda _, pg_id=item.id_plan_generado,
                                              plan_n=item.nombre_plan,
                                              per_n=item.nombre_periodo:
                                    self._ver_horario(pg_id, plan_n, per_n),
                            ),
                            # Editar — navegar a DetallePlanView
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=Colores.AZUL_PRIMARIO,
                                icon_size=18,
                                tooltip="Editar",
                                on_click=lambda _, pg_id=item.id_plan_generado:
                                    self._editar(pg_id),
                            ),
                            # Eliminar — confirmación
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINED,
                                icon_color=Colores.ROJO,
                                icon_size=18,
                                tooltip="Eliminar",
                                on_click=lambda _, pg_id=item.id_plan_generado:
                                    self._confirmar_eliminar(pg_id),
                            ),
                        ],
                        spacing=0,
                    )),
                ],
                on_select_changed=lambda _, it=item: self._on_row_selected(it),
            )
            for item in items
        ]

        # Resetear selección
        self._btn_exportar.disabled = True
        self._lbl_seleccion.value = "Selecciona una fila para exportar"
        self._lbl_seleccion.color = Colores.TEXTO_MUTED
        self._lbl_seleccion.italic = True

        if self.page:
            self._tabla.update()
            self._btn_exportar.update()
            self._lbl_seleccion.update()

    # ── Filtros ───────────────────────────────────────────────

    def _on_filtro_cambiado(self, _) -> None:
        pass  # aplicar filtro al buscar explícitamente

    def _aplicar_filtros(self) -> None:
        """Filtra la lista del historial según los dropdowns activos.
        Solo muestra resultados si al menos un filtro está activo."""
        grado   = self._dd_grado.value
        plan    = self._dd_plan.value
        periodo = self._dd_periodo.value
        semestre = self._dd_semestre.value

        if not any([grado, plan, periodo, semestre]):
            self._msg("Selecciona al menos un filtro antes de buscar.")
            return

        filtrado = [
            item for item in self._todos
            if (not grado   or item.nombre_nivel  == grado)
            and (not plan    or item.nombre_plan   == plan)
            and (not periodo or item.nombre_periodo == periodo)
        ]
        # Re-enumerar claves con el filtrado
        for idx, item in enumerate(filtrado, start=1):
            item.clave = str(idx).zfill(3)

        self._renderizar_tabla(filtrado)

        # Mostrar panel de tabla
        self._panel_tabla.visible = True
        if self.page:
            self._panel_tabla.update()

    def _limpiar_filtros(self) -> None:
        """Limpia todos los dropdowns de filtro y oculta la tabla."""
        self._dd_grado.value   = None
        self._dd_plan.value    = None
        self._dd_periodo.value = None
        self._dd_semestre.value = None

        # Ocultar tabla y limpiar selección
        self._tabla.rows = []
        self._filtrado = []
        self._selected_item = None
        self._panel_tabla.visible = False
        self._btn_exportar.disabled = True
        self._lbl_seleccion.value = "Selecciona una fila para exportar"
        self._lbl_seleccion.color = Colores.TEXTO_MUTED
        self._lbl_seleccion.italic = True

        if self.page:
            self._dd_grado.update()
            self._dd_plan.update()
            self._dd_periodo.update()
            self._dd_semestre.update()
            self._tabla.update()
            self._panel_tabla.update()
            self._btn_exportar.update()
            self._lbl_seleccion.update()

        # Recargar datos de filtros desde BD
        self._cargar_datos()

    # ── Ver horario (popup) ───────────────────────────────────

    def _ver_horario(
        self,
        id_plan_generado: int,
        nombre_plan: str,
        nombre_periodo: str,
    ) -> None:
        """Genera el PDF del plan correspondiente y lo muestra en un popup."""
        # Obtener id_plan desde el plan_generado
        id_plan = self._service.obtener_id_plan_de_plan_generado(id_plan_generado)
        if id_plan is None:
            self._msg("No se encontró el plan asociado.")
            return

        if not self._ruta_membrete:
            self._msg("Selecciona un membrete en la pestaña 'Planes de estudios' "
                      "antes de previsualizar.")
            return

        ruta_pdf = os.path.join(
            tempfile.gettempdir(),
            f"historial_preview_{id_plan_generado}.pdf",
        )

        try:
            from ui.pdf.generador_pdf import GeneradorPDF
            registros = self._service.obtener_horarios(id_plan)
            if not registros:
                self._msg("No hay horarios registrados para este plan.")
                return
            GeneradorPDF(
                horarios=registros,
                nombre_plan=nombre_plan,
                nombre_lies="",
                ruta_membrete=self._ruta_membrete,
                ruta_salida=ruta_pdf,
            ).generar()
        except Exception as e:
            self._msg(f"Error al generar PDF: {e}")
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
                title=ft.Text(
                    f"Vista previa — {nombre_plan} | {nombre_periodo}",
                    font_family=Fuentes.TITULO,
                    size=16,
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
            self._msg("PyMuPDF no está instalado. Instala con: pip install pymupdf")
        except Exception as e:
            self._msg(f"Error al mostrar vista previa: {e}")

    # ── Editar ────────────────────────────────────────────────

    def _editar(self, id_plan_generado: int) -> None:
        """Navega a la pantalla de edición (DetallePlanView) del plan."""
        id_plan = self._service.obtener_id_plan_de_plan_generado(id_plan_generado)
        if id_plan is None:
            self._msg("No se encontró el plan asociado.")
            return
        self._on_editar_plan(id_plan)

    # ── Eliminar ──────────────────────────────────────────────

    def _confirmar_eliminar(self, id_plan_generado: int) -> None:
        """Muestra el diálogo «¿Estás seguro?» antes de eliminar."""
        self._page.open(DialogoConfirmacion(
            page=self._page,
            on_confirmar=lambda: self._eliminar(id_plan_generado),
        ))

    def _eliminar(self, id_plan_generado: int) -> None:
        """Elimina el plan_generado y sus horarios, luego recarga la tabla."""
        ok, msg = self._service.eliminar_plan_generado(id_plan_generado)
        self._msg(msg)
        if ok:
            # Recargar datos y re-aplicar filtros si estaban activos
            self._cargar_datos()
            grado   = self._dd_grado.value
            plan    = self._dd_plan.value
            periodo = self._dd_periodo.value
            semestre = self._dd_semestre.value
            if any([grado, plan, periodo, semestre]):
                self._aplicar_filtros()
            else:
                self._panel_tabla.visible = False
                if self.page:
                    self._panel_tabla.update()

    # ── Selección de fila ─────────────────────────────────────

    def _on_row_selected(self, item) -> None:
        """Resalta la fila seleccionada en azul y habilita exportar."""
        self._selected_item = item

        for row in self._tabla.rows:
            row.selected = False
            row.color = None

        # Buscar la fila correspondiente al item
        for i, it in enumerate(self._filtrado):
            if it is item and i < len(self._tabla.rows):
                self._tabla.rows[i].color = "#D6E4FF"
                self._tabla.rows[i].selected = True
                break

        self._btn_exportar.disabled = False
        self._lbl_seleccion.value = f"\u2713 {item.nombre_plan} seleccionado"
        self._lbl_seleccion.color = Colores.AZUL_PRIMARIO
        self._lbl_seleccion.italic = False

        if self.page:
            self._tabla.update()
            self._btn_exportar.update()
            self._lbl_seleccion.update()

    def _exportar(self) -> None:
        """Abre diálogo del sistema para elegir dónde guardar el PDF."""
        if not self._selected_item:
            self._msg("Selecciona una fila de la tabla primero.")
            return

        if not self._ruta_membrete:
            self._msg(
                "Selecciona un membrete en la pestaña 'Planes de estudios' "
                "antes de exportar."
            )
            return

        item = self._selected_item
        id_plan = self._service.obtener_id_plan_de_plan_generado(
            item.id_plan_generado
        )
        if id_plan is None:
            self._msg("No se encontró el plan asociado.")
            return

        registros = self._service.obtener_horarios(id_plan)
        if not registros:
            self._msg("No hay horarios registrados para este plan.")
            return

        # Nombre sugerido para el archivo
        nombre_archivo = (
            f"horario_{item.nombre_plan}_{item.nombre_periodo}.pdf"
            .replace(" ", "_")
        )

        self._save_picker.save_file(
            dialog_title="Guardar PDF de horario",
            file_name=nombre_archivo,
            allowed_extensions=["pdf"],
        )

    def _on_save_result(self, e: ft.FilePickerResultEvent) -> None:
        """Callback del FilePicker — genera el PDF en la ruta seleccionada."""
        if not e.path:
            return

        ruta = e.path
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        item = self._selected_item
        if not item:
            self._msg("No hay un plan seleccionado.")
            return

        id_plan = self._service.obtener_id_plan_de_plan_generado(
            item.id_plan_generado
        )
        if id_plan is None:
            self._msg("No se encontró el plan asociado.")
            return

        try:
            from ui.pdf.generador_pdf import GeneradorPDF

            registros = self._service.obtener_horarios(id_plan)
            if not registros:
                self._msg("No hay horarios registrados para este plan.")
                return

            # Generar PDF en un temporal y luego copiar a la ruta elegida
            ruta_tmp = os.path.join(
                tempfile.gettempdir(),
                f"export_{item.id_plan_generado}.pdf",
            )
            GeneradorPDF(
                horarios=registros,
                nombre_plan=item.nombre_plan,
                nombre_lies="",
                ruta_membrete=self._ruta_membrete,
                ruta_salida=ruta_tmp,
            ).generar()

            # Copiar al destino elegido por el usuario
            shutil.copy2(ruta_tmp, ruta)
            self._msg(f"PDF guardado en: {ruta}")
        except Exception as exc:
            self._msg(f"Error al exportar PDF: {exc}")

    # ── Helpers ───────────────────────────────────────────────

    def _msg(self, texto: str) -> None:
        self._page.open(ft.SnackBar(content=ft.Text(texto)))
