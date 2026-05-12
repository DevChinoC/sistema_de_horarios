"""crear_plan_view.py
Vista 'Crear plan de estudios' — panel embebido dentro de PlanesView.

Cambios respecto a la versión anterior:
  1. Ya no tiene barra de navegación propia; se embebe dentro de
     PlanesView y comparte la BarraTabs de esa vista.
  2. Botón "Cancelar" eliminado; solo queda "Guardar" centrado.
  3. El membrete se guarda dentro del proyecto en
     ui/membretes/<id_plan>/<membrete>.<ext>.
     La ruta local (dentro del proyecto) es lo que se persiste en BD.
"""

import flet as ft
import datetime
import calendar
import threading
from typing import Callable

from application.services.plan_estudios_service import PlanEstudiosService
from application.dto.plan_estudios_dto import CrearPlanDTO, FilaMateriaDTO
from ui.components.plan_components import (
    Colores, Fuentes, SelectorGrado, TablaMaterias,
    BotonPrimario,
)

# Anchos fijos para los campos superiores (compactos)
_ANCHO_NOMBRE = 300
_ANCHO_FECHA  = 190


# ════════════════════════════════════════════════════════════
# Calendario inline – se agrega a page.overlay para flotar
# ════════════════════════════════════════════════════════════
_DIAS_SEMANA = ["Dom", "Lun", "Mar", "Miér", "Jue", "Vier", "Sáb"]
_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


class _CalendarioOverlay(ft.Container):
    """Calendario flotante que vive en page.overlay.

    Al abrirse muestra un fondo semitransparente que cierra el calendario
    al hacer clic fuera.  Todo el panel recibe clics correctamente porque
    page.overlay está por encima de cualquier layout.
    """

    _ANCHO_CAL = 280

    def __init__(self, on_fecha: Callable[[datetime.date], None]) -> None:
        self._on_fecha = on_fecha
        hoy = datetime.date.today()
        self._mes = hoy.month
        self._anio = hoy.year

        # ── Dropdown de mes ───────────────────────────────────
        self._dd_mes = ft.Dropdown(
            value=_MESES[self._mes - 1],
            options=[
                ft.dropdown.Option(
                    key=m, text=m,
                    text_style=ft.TextStyle(
                        size=12, color=Colores.TEXTO,
                        font_family=Fuentes.CAMPOS),
                    alignment=ft.alignment.center_left,
                ) for m in _MESES
            ],
            on_change=self._cambiar_mes_dd,
            width=140,
            text_size=13,
            dense=True,
            item_height=36,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_color="transparent",
            fill_color="transparent",
            bgcolor=Colores.BLANCO,
            color=Colores.TEXTO,
            menu_height=250,
            text_style=ft.TextStyle(
                font_family=Fuentes.CAMPOS, weight=ft.FontWeight.W_600),
        )

        # ── Año con flechas ───────────────────────────────────
        self._lbl_anio = ft.Text(
            str(self._anio), size=13, weight=ft.FontWeight.W_600,
            color=Colores.AZUL_PRIMARIO, font_family=Fuentes.CAMPOS,
        )
        cabecera = ft.Row(
            controls=[
                self._dd_mes,
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.CHEVRON_LEFT, icon_size=18,
                            icon_color=Colores.AZUL_PRIMARIO,
                            on_click=self._anio_ant,
                            style=ft.ButtonStyle(padding=ft.padding.all(0)),
                            width=28, height=28,
                        ),
                        self._lbl_anio,
                        ft.IconButton(
                            icon=ft.Icons.CHEVRON_RIGHT, icon_size=18,
                            icon_color=Colores.AZUL_PRIMARIO,
                            on_click=self._anio_sig,
                            style=ft.ButtonStyle(padding=ft.padding.all(0)),
                            width=28, height=28,
                        ),
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # ── Encabezados Dom–Sáb ───────────────────────────────
        dias_header = ft.Row(
            controls=[
                ft.Container(
                    width=36, height=24, alignment=ft.alignment.center,
                    content=ft.Text(
                        d, size=11, weight=ft.FontWeight.W_600,
                        color=Colores.AZUL_PRIMARIO,
                        font_family=Fuentes.CAMPOS,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ) for d in _DIAS_SEMANA
            ],
            spacing=2, alignment=ft.MainAxisAlignment.CENTER,
        )

        # ── Grilla de días ────────────────────────────────────
        self._grid_dias = ft.Column(spacing=2)

        # ── Panel del calendario ──────────────────────────────
        panel_cal = ft.Container(
            content=ft.Column(
                controls=[cabecera, dias_header, self._grid_dias],
                spacing=6,
            ),
            width=self._ANCHO_CAL,
            padding=ft.padding.all(12),
            bgcolor=Colores.BLANCO,
            border=ft.border.all(1.5, Colores.AZUL_PRIMARIO),
            border_radius=ft.border_radius.all(10),
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=8,
                color="#1A000000", offset=ft.Offset(0, 2),
            ),
        )

        # ── Fondo semitransparente (click-to-close) ───────────
        fondo = ft.Container(
            expand=True,
            bgcolor="#05000000",
            on_click=lambda _: self.cerrar(),
        )

        # ── Layout: fondo + panel posicionado arriba a la derecha ─
        super().__init__(
            content=ft.Stack(
                controls=[
                    fondo,
                    ft.Container(
                        content=panel_cal,
                        top=120,
                        right=80,
                    ),
                ],
            ),
            expand=True,
            visible=False,
        )
        self._construir_grid()

    # ── Grid ──────────────────────────────────────────────────
    def _construir_grid(self) -> None:
        self._grid_dias.controls.clear()
        cal = calendar.Calendar(firstweekday=6)   # Domingo primero
        semanas = cal.monthdayscalendar(self._anio, self._mes)

        # Días del mes anterior (para rellenar primera semana)
        prev_m = 12 if self._mes == 1 else self._mes - 1
        prev_a = self._anio - 1 if self._mes == 1 else self._anio
        _, dias_prev = calendar.monthrange(prev_a, prev_m)

        dia_next = 1
        for i, semana in enumerate(semanas):
            celdas = []
            for j, dia in enumerate(semana):
                if dia == 0:
                    if i == 0:
                        ceros = semana[:j + 1].count(0)
                        dia_show = dias_prev - (semana.count(0) - ceros)
                    else:
                        dia_show = dia_next
                        dia_next += 1
                    celdas.append(ft.Container(
                        width=36, height=30,
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            str(dia_show), size=12,
                            color=Colores.TEXTO_MUTED,
                            font_family=Fuentes.CAMPOS,
                            text_align=ft.TextAlign.CENTER),
                    ))
                else:
                    celdas.append(ft.Container(
                        width=36, height=30,
                        alignment=ft.alignment.center,
                        border_radius=4,
                        ink=True,
                        on_click=lambda _, d=dia: self._seleccionar_dia(d),
                        content=ft.Text(
                            str(dia), size=12,
                            color=Colores.TEXTO,
                            font_family=Fuentes.CAMPOS,
                            text_align=ft.TextAlign.CENTER),
                    ))
            self._grid_dias.controls.append(
                ft.Row(controls=celdas, spacing=2,
                       alignment=ft.MainAxisAlignment.CENTER))

    def _refrescar(self) -> None:
        self._dd_mes.value = _MESES[self._mes - 1]
        self._lbl_anio.value = str(self._anio)
        self._construir_grid()
        if self.page:
            self.update()

    # ── Navegación ────────────────────────────────────────────
    def _cambiar_mes_dd(self, e) -> None:
        self._mes = _MESES.index(e.control.value) + 1
        self._refrescar()

    def _anio_ant(self, _) -> None:
        self._anio -= 1
        self._refrescar()

    def _anio_sig(self, _) -> None:
        self._anio += 1
        self._refrescar()

    # ── Selección ─────────────────────────────────────────────
    def _seleccionar_dia(self, dia: int) -> None:
        fecha = datetime.date(self._anio, self._mes, dia)
        self.cerrar()
        self._on_fecha(fecha)

    # ── Abrir / Cerrar ────────────────────────────────────────
    def abrir(self) -> None:
        self.visible = True
        if self.page:
            self.update()

    def cerrar(self) -> None:
        self.visible = False
        if self.page:
            self.update()

    def toggle(self) -> None:
        if self.visible:
            self.cerrar()
        else:
            self.abrir()



class CrearPlanView(ft.Container):
    """Vista 'Crear plan de estudios' — panel embebido en PlanesView.

    • Se integra como panel dentro del área de contenido de PlanesView,
      compartiendo la misma BarraTabs que las demás pestañas.
    • Solo tiene el botón 'Guardar' (sin Cancelar), centrado.
    • El membrete se guarda en ui/membretes/<id_plan>/ dentro del
      proyecto; la ruta local se persiste en BD.

    Reglas de negocio:
    • Si el grado es MIIDT → el plan se asocia a TODAS las LIES.
    • Si el grado NO es MIIDT → el plan se asocia solo a la primera LIES.
    • Tipo Optativa → semestre fijo en 0 (bloqueado).
    • Tipo Tronco   → semestre 1-8 (opción 0 no aparece).
    • Fila inicial vacía: solo hint_text, sin texto prefijado.
    """

    def __init__(
        self,
        page: ft.Page,
        service: PlanEstudiosService,
        lies_activa: dict,
        on_guardado: Callable | None = None,
        on_cancelado: Callable | None = None,
        on_membrete_seleccionado: Callable | None = None,
    ) -> None:
        self._page         = page
        self._service      = service
        self._lies_activa  = lies_activa
        self._on_guardado  = on_guardado
        self._on_cancelado = on_cancelado
        self._on_membrete_seleccionado = on_membrete_seleccionado
        self._ruta_membrete: str | None = None

        # ── Datos de la BD ────────────────────────────────────
        tipos   = self._service.obtener_tipos_materia()
        niveles = self._service.obtener_niveles()
        self._nivel_map: dict[str, int] = {n["nombre"]: n["id"] for n in niveles}
        self._todas_lies = self._service.obtener_lies()

        # ── Componentes ───────────────────────────────────────
        self._selector_grado = SelectorGrado(
            niveles=niveles,
            on_change=self._on_grado_cambiado,
            on_crear_nivel=self._crear_nivel,
        )

        self._campo_nombre = ft.TextField(
            hint_text="Nombre del plan....",
            hint_style=ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            bgcolor=Colores.BLANCO,
            color=Colores.TEXTO,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=10),
            text_size=13,
            width=_ANCHO_NOMBRE,
            text_style=ft.TextStyle(color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
        )

        self._calendario = _CalendarioOverlay(
            on_fecha=self._on_fecha_seleccionada,
        )

        self._campo_fecha = ft.TextField(
            hint_text="DD/MM/AA",
            hint_style=ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            bgcolor=Colores.BLANCO,
            color=Colores.TEXTO,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=10),
            text_size=13,
            width=_ANCHO_FECHA,
            read_only=True,
            on_click=self._toggle_calendario,
            text_style=ft.TextStyle(color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                icon_color=Colores.AZUL_PRIMARIO,
                icon_size=20,
                on_click=self._toggle_calendario,
                style=ft.ButtonStyle(padding=ft.padding.all(0)),
            ),
        )

        # Tabla: fila inicial vacía (hint_text, sin texto prefijado)
        self._tabla = TablaMaterias(tipos=tipos, altura= 300)
        self._tabla.agregar_fila(nombre="", id_tipo=0, semestre=0)

        # ── Selector de membrete ─────────────────────────────
        self._lbl_membrete = ft.Text(
            "Sin membrete cargado", size=12,
            color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS,
            italic=True,
        )
        self._file_picker = ft.FilePicker(on_result=self._on_membrete_resultado)

        btn_membrete = ft.ElevatedButton(
            text="Seleccionar membrete",
            icon=ft.Icons.IMAGE_OUTLINED,
            bgcolor=Colores.AZUL_PRIMARIO,
            color=Colores.BLANCO,
            elevation=0,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                text_style=ft.TextStyle(size=12, font_family=Fuentes.CAMPOS),
            ),
            on_click=lambda _: self._file_picker.pick_files(
                dialog_title="Seleccionar imagen de membrete",
                allowed_extensions=["png", "jpg", "jpeg"],
                allow_multiple=False,
            ),
        )

        bloque_membrete = ft.Column(
            controls=[
                ft.Text(
                    "Membrete:", size=13, weight=ft.FontWeight.W_600,
                    color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
                ),
                ft.Row(
                    controls=[btn_membrete, self._lbl_membrete],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=6,
        )

        # ════════════════════ LAYOUT ═════════════════════════

        # 1) Etiquetas + campos
        bloque_nombre = ft.Column(
            controls=[
                ft.Text(
                    "Nombre del plan:", size=13,
                    weight=ft.FontWeight.W_600, color=Colores.TEXTO,
                    font_family=Fuentes.CAMPOS,
                ),
                self._campo_nombre,
            ],
            spacing=4,
        )
        bloque_fecha = ft.Column(
            controls=[
                ft.Text(
                    "Fecha de inicio", size=13,
                    weight=ft.FontWeight.W_600, color=Colores.TEXTO,
                    font_family=Fuentes.CAMPOS,
                ),
                self._campo_fecha,
            ],
            spacing=4,
        )

        # 2) Bloque de ancho fijo centrado (= ancho de la tabla 520px)
        ancho_bloque = TablaMaterias.ANCHO_TABLA

        bloque_fijo = ft.Container(
            width=ancho_bloque,
            bgcolor=Colores.BLANCO,
            content=ft.Column(
                controls=[
                    ft.Container(height=20),
                    self._selector_grado,
                    ft.Container(height=12),
                    ft.Row(
                        controls=[bloque_nombre, bloque_fecha],
                        spacing=20,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.Container(height=12),
                    bloque_membrete,
                    ft.Container(height=8),
                    self._tabla,
                       
                    
                ],
                spacing=0,
            ),
        )

        contenido = ft.Container(
            content=bloque_fijo,
            bgcolor=Colores.BLANCO,
            alignment=ft.alignment.top_center,
            expand=True,
        )

        # 3) Solo botón "Guardar", centrado
        barra_botones = ft.Container(
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(top=20, bottom=28),
            alignment=ft.alignment.top_center,
            content=ft.Container(
                width=ancho_bloque,
                content=ft.Row(
                    controls=[
                        BotonPrimario(texto="Guardar", on_click=self._guardar),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ),
        )

        super().__init__(
            content=ft.Column(
                controls=[contenido, barra_botones],
                spacing=0,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            bgcolor=Colores.BLANCO,
        )

    # ── Ciclo de vida ─────────────────────────────────────────

    def did_mount(self) -> None:
        """Registra FilePicker y calendario en page.overlay."""
        if self._file_picker not in self._page.overlay:
            self._page.overlay.append(self._file_picker)
        if self._calendario not in self._page.overlay:
            self._page.overlay.append(self._calendario)
        self._page.update()

    def will_unmount(self) -> None:
        """Limpia FilePicker y calendario del overlay."""
        if self._file_picker in self._page.overlay:
            self._page.overlay.remove(self._file_picker)
        if self._calendario in self._page.overlay:
            self._page.overlay.remove(self._calendario)
        self._page.update()

    # ── Callbacks ─────────────────────────────────────────────

    def _toggle_calendario(self, _) -> None:
        """Muestra u oculta el calendario flotante."""
        self._calendario.toggle()

    def _on_fecha_seleccionada(self, fecha: datetime.date) -> None:
        """Callback cuando el usuario elige una fecha en el calendario."""
        self._campo_fecha.value = fecha.strftime("%d/%m/%y")
        if self.page:
            self._campo_fecha.update()

    def _on_grado_cambiado(self, nombre: str, id_nivel: int | None) -> None:
        if id_nivel is not None:
            self._nivel_map[nombre] = id_nivel

    def _crear_nivel(self, nombre: str) -> dict | None:
        resultado = self._service.crear_nivel(nombre)
        if resultado:
            self._nivel_map[resultado["nombre"]] = resultado["id"]
        return resultado



    def _guardar(self, _) -> None:
        nombre   = (self._campo_nombre.value or "").strip()
        grado    = self._selector_grado.valor
        id_nivel = self._selector_grado.id_valor

        if id_nivel is None:
            id_nivel = self._nivel_map.get(grado)
        if id_nivel is None:
            self._mostrar_mensaje(f"Nivel '{grado}' no existe en la BD.")
            return
        if not nombre:
            self._mostrar_mensaje("El nombre del plan no puede estar vacío.")
            return

        filas = self._tabla.obtener_filas()
        if not filas:
            self._mostrar_mensaje("Agrega al menos una materia completa.")
            return

        if self._ruta_membrete is None:
            self._mostrar_mensaje("Selecciona un membrete antes de guardar.")
            return

        # LIES: solo MIIDT usa todas; otros grados → solo la primera
        _NIVEL_CON_LIES = "MIIDT"
        if grado.upper() == _NIVEL_CON_LIES:
            lies_ids = [l["id"] for l in self._todas_lies]
        else:
            lies_ids = [self._todas_lies[0]["id"]] if self._todas_lies else []

        if not lies_ids:
            self._mostrar_mensaje("No hay LIES registradas en la BD.")
            return

        dto = CrearPlanDTO(
            nombre=nombre,
            id_nivel=id_nivel,
            lies_ids=lies_ids,
            filas=[
                FilaMateriaDTO(f["nombre_materia"], f["id_tipo"], f["numero_semestre"])
                for f in filas
            ],
            # ruta_membrete = ruta temporal del picker; el service la copiará
            # a ui/membretes/<id_plan>/ y guardará la ruta local en BD.
            ruta_membrete=self._ruta_membrete,
        )
        exito, msg = self._service.crear_plan(dto)
        if exito:
            self._mostrar_exito()
        else:
            self._mostrar_mensaje(msg)

    def _mostrar_exito(self) -> None:
        """Superpone palomita + texto sobre la pantalla 2 s y luego navega."""

        overlay = ft.Container(
            expand=True,
            bgcolor="#AA000000",
            alignment=ft.alignment.center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#22C55E", size=100),
                    ft.Text(
                        "¡Plan guardado!",
                        size=20,
                        weight=ft.FontWeight.W_600,
                        color=Colores.BLANCO,
                        font_family=Fuentes.CAMPOS,
                    ),
                ],
            ),
        )

        self._page.overlay.append(overlay)
        self._page.update()

        def _quitar_y_navegar():
            import time
            time.sleep(2)
            self._page.overlay.remove(overlay)
            self._page.update()
            if self._on_guardado:
                self._on_guardado()

        threading.Thread(target=_quitar_y_navegar, daemon=True).start()

    def _on_membrete_resultado(self, e: ft.FilePickerResultEvent) -> None:
        """Callback del FilePicker de membrete."""
        if e.files:
            self._ruta_membrete = e.files[0].path
            nombre = e.files[0].name
            self._lbl_membrete.value  = nombre
            self._lbl_membrete.color  = Colores.TEXTO
            self._lbl_membrete.italic = False
        else:
            self._ruta_membrete = None
            self._lbl_membrete.value  = "Sin membrete cargado"
            self._lbl_membrete.color  = Colores.TEXTO_MUTED
            self._lbl_membrete.italic = True
        if self.page:
            self._lbl_membrete.update()
        # Notificar al exterior (p. ej. para preview o tests)
        if self._on_membrete_seleccionado:
            self._on_membrete_seleccionado(self._ruta_membrete)

    def _mostrar_mensaje(self, texto: str) -> None:
        print(f"[CrearPlanView] {texto}")
        self._page.open(ft.SnackBar(content=ft.Text(texto)))
