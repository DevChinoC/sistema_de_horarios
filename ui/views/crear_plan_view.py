import flet as ft
import threading
from typing import Callable

from application.services.plan_estudios_service import PlanEstudiosService
from application.dto.plan_estudios_dto import CrearPlanDTO, FilaMateriaDTO
from ui.components.plan_components import (
    Colores, Fuentes, CabeceraPlan, SelectorGrado, TablaMaterias,
    BotonPrimario, DialogoConfirmacion,
)

# Anchos fijos para los campos superiores (compactos)
_ANCHO_NOMBRE = 300
_ANCHO_FECHA  = 190


class CrearPlanView(ft.Column):
    """Vista 'Crear plan de estudios'.

    Toda la UI se agrupa en un bloque de ancho fijo (igual al de la tabla,
    520px) que se centra horizontalmente en la ventana. Esto garantiza que
    Grado, campos Nombre/Fecha, tabla y botones estén perfectamente alineados.

    Reglas de negocio:
    • Plan engloba TODAS las LIES de la BD.
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
            text_style=ft.TextStyle(color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
        )

        # Tabla: fila inicial vacía (hint_text, sin texto prefijado)
        self._tabla = TablaMaterias(tipos=tipos)
        self._tabla.agregar_fila(nombre="", id_tipo=0, semestre=0)

        # ── Selector de membrete ─────────────────────────────────
        self._lbl_membrete = ft.Text(
            "Sin membrete cargado", size=12,
            color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS,
            italic=True,
        )
        self._file_picker = ft.FilePicker(
            on_result=self._on_membrete_resultado)
        page.overlay.append(self._file_picker)

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
                ft.Text("Membrete:", size=13, weight=ft.FontWeight.W_600,
                        color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
                ft.Row(
                    controls=[btn_membrete, self._lbl_membrete],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=6,
        )

        # ════════════════════ LAYOUT ═════════════════════════

        # 1) Header fijo
        header = CabeceraPlan(on_cerrar=self._cerrar)

        # 2) Etiquetas + campos
        bloque_nombre = ft.Column(
            controls=[
                ft.Text("Nombre del plan:", size=13,
                        weight=ft.FontWeight.W_600, color=Colores.TEXTO,
                        font_family=Fuentes.CAMPOS),
                self._campo_nombre,
            ],
            spacing=4,
        )
        bloque_fecha = ft.Column(
            controls=[
                ft.Text("Fecha de inicio", size=13,
                        weight=ft.FontWeight.W_600, color=Colores.TEXTO,
                        font_family=Fuentes.CAMPOS),
                self._campo_fecha,
            ],
            spacing=4,
        )

        # 3) Bloque de ancho fijo = ancho de la tabla (520px).
        #    Al centrarlo en pantalla, TODO queda alineado: grado, campos y tabla.
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

        # Centrar el bloque fijo en el espacio disponible
        contenido = ft.Container(
            content=bloque_fijo,
            bgcolor=Colores.BLANCO,
            alignment=ft.alignment.top_center,
            expand=True,
        )

        # 4) Botones centrados al mismo ancho que el bloque
        barra_botones = ft.Container(
            bgcolor=Colores.BLANCO,
            padding=ft.padding.only(top=20, bottom=28),
            alignment=ft.alignment.top_center,
            content=ft.Container(
                width=ancho_bloque,
                content=ft.Row(
                    controls=[
                        BotonPrimario(texto="Guardar", on_click=self._guardar),
                        BotonPrimario(texto="Cancelar",
                                      on_click=self._confirmar_cancelar,
                                      color=Colores.ROJO),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
            ),
        )

        super().__init__(
            controls=[header, contenido, barra_botones],
            spacing=0,
            expand=True,
        )

    # ── Callbacks ─────────────────────────────────────────────

    def _on_grado_cambiado(self, nombre: str, id_nivel: int | None) -> None:
        if id_nivel is not None:
            self._nivel_map[nombre] = id_nivel

    def _crear_nivel(self, nombre: str) -> dict | None:
        resultado = self._service.crear_nivel(nombre)
        if resultado:
            self._nivel_map[resultado["nombre"]] = resultado["id"]
        return resultado

    def _cerrar(self, _=None) -> None:
        if self._on_cancelado:
            self._on_cancelado()

    def _confirmar_cancelar(self, _=None) -> None:
        self._page.open(DialogoConfirmacion(
            page=self._page,
            on_confirmar=self._ejecutar_cancelar,
        ))

    def _ejecutar_cancelar(self) -> None:
        if self._on_cancelado:
            self._on_cancelado()

    def _limpiar_vista(self) -> None:
        self._page.controls.clear()
        self._page.update()

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

        all_lies_ids = [l["id"] for l in self._todas_lies]

        dto = CrearPlanDTO(
            nombre=nombre,
            id_nivel=id_nivel,
            lies_ids=all_lies_ids,
            filas=[
                FilaMateriaDTO(f["nombre_materia"], f["id_tipo"], f["numero_semestre"])
                for f in filas
            ],
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
            bgcolor="#AA000000",          # fondo semitransparente negro
            alignment=ft.alignment.center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE,
                            color="#22C55E", size=100),
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

        # Agregar overlay encima de todo
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
            self._lbl_membrete.value = nombre
            self._lbl_membrete.color = Colores.TEXTO
            self._lbl_membrete.italic = False
        else:
            self._ruta_membrete = None
            self._lbl_membrete.value = "Sin membrete cargado"
            self._lbl_membrete.color = Colores.TEXTO_MUTED
            self._lbl_membrete.italic = True
        if self.page:
            self._lbl_membrete.update()
        # Notificar al Navegador
        if self._on_membrete_seleccionado:
            self._on_membrete_seleccionado(self._ruta_membrete)

    def _mostrar_mensaje(self, texto: str) -> None:
        self._page.open(ft.SnackBar(content=ft.Text(texto)))
