import flet as ft
from typing import Callable

from application.services.planes_service import PlanesService
from application.services.plan_estudios_service import PlanEstudiosService
from application.services.horario_service import HorarioService
from application.dto.planes_dto import NivelDTO, PlanDTO
from ui.components.plan_components import Colores, Fuentes, BotonPrimario
from ui.components.puerta_animada import PuertaAnimada
from ui.views.horario_docente_view import HorarioDocenteView
from ui.views.historial_view import HistorialView
from ui.views.crear_plan_view import CrearPlanView


# ─────────────────────────────────────────────────────────────
# Cabecera de la vista principal
# ─────────────────────────────────────────────────────────────
class CabeceraApp(ft.Container):
    """Icono | Título centrado | X roja cuadrada."""

    def __init__(self, on_cerrar: Callable) -> None:
        icono = ft.Icon(
            ft.Icons.CALENDAR_MONTH,
            color=Colores.AZUL_PRIMARIO, size=36,
        )
        titulo = ft.Text(
            "Gestión de planes y horarios",
            size=24, weight=ft.FontWeight.W_400,
            color=Colores.AZUL_PRIMARIO,
            font_family=Fuentes.TITULO,
            text_align=ft.TextAlign.CENTER,
            expand=True,
        )
        boton_x = ft.IconButton(
            icon=ft.Icons.CLOSE, icon_color=Colores.BLANCO,
            bgcolor=ft.Colors.RED, icon_size=18, on_click=on_cerrar,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),
                padding=ft.padding.all(8),
            ),
        )

        super().__init__(
            content=ft.Row(
                controls=[icono, titulo, boton_x],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colores.BLANCO,
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            border=ft.border.only(bottom=ft.BorderSide(3, Colores.AZUL_PRIMARIO)),
        )


# ─────────────────────────────────────────────────────────────
# Barra de pestañas (Tabs)
# ─────────────────────────────────────────────────────────────
class BarraTabs(ft.Row):
    """Pestañas: Planes de estudios | Crear plan | Horario por docente | Historial."""

    _TABS = ["Planes de estudios", "Crear plan", "Horario por docente", "Historial"]

    def __init__(self, on_tab: Callable[[str], None]) -> None:
        self._on_tab = on_tab
        self._activo = self._TABS[0]
        self._botones: list[ft.OutlinedButton] = []

        super().__init__(
            controls=self._construir(),
            spacing=35,
        )

    def _construir(self) -> list[ft.Control]:
        self._botones.clear()
        for tab in self._TABS:
            activo = tab == self._activo
            btn = ft.OutlinedButton(
                text=tab,
                width=200,
                on_click=lambda e, t=tab: self._seleccionar(t),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.padding.symmetric(horizontal=20, vertical=14),
                    bgcolor=Colores.AZUL_PRIMARIO if activo else Colores.BLANCO,
                    color=Colores.BLANCO if activo else Colores.AZUL_PRIMARIO,
                    side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                    text_style=ft.TextStyle(
                        size=14,
                        font_family=Fuentes.CAMPOS,
                        weight=ft.FontWeight.W_500,
                    ),
                ),
            )
            self._botones.append(btn)
        return self._botones

    def _seleccionar(self, tab: str) -> None:
        self._activo = tab
        for btn in self._botones:
            activo = btn.text == self._activo
            btn.style.bgcolor = Colores.AZUL_PRIMARIO if activo else Colores.BLANCO
            btn.style.color   = Colores.BLANCO if activo else Colores.AZUL_PRIMARIO
        if self.page:
            self.update()
        self._on_tab(tab)

    def seleccionar_tab(self, tab: str) -> None:
        """Selecciona un tab programáticamente."""
        self._seleccionar(tab)


# ─────────────────────────────────────────────────────────────
# Panel "Planes de estudios" — dropdowns + puerta
# ─────────────────────────────────────────────────────────────
class PanelPlanesEstudios(ft.Container):
    """Panel con selector de Grado, selector de Plan y puerta animada.

    Al abrir la puerta se llama on_abrir_plan(plan: PlanDTO).
    """

    def __init__(
        self,
        page: ft.Page,
        service: PlanesService,
        on_abrir_plan: Callable[[PlanDTO], None],
    ) -> None:
        self._page          = page
        self._service       = service
        self._on_abrir_plan = on_abrir_plan
        self._plan_actual: PlanDTO | None = None

        # ── Dropdown Grado ────────────────────────────────────
        self._dd_grado = ft.Dropdown(
            hint_text="Seleccionar grado",
            hint_style=ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            options=[],
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            bgcolor=Colores.BLANCO,
            fill_color=Colores.BLANCO,
            color=Colores.TEXTO,
            text_size=13,
            width=200,
            menu_height=150,
            text_style=ft.TextStyle(
                color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
            on_change=self._on_grado_cambiado,
        )

        # ── Dropdown Plan ─────────────────────────────────────
        self._dd_plan = ft.Dropdown(
            hint_text="Seleccionar Plan",
            hint_style=ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            options=[],
            disabled=True,
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            bgcolor=Colores.BLANCO,
            fill_color=Colores.BLANCO,
            color=Colores.TEXTO,
            text_size=13,
            width=200,
            menu_height=150,
            text_style=ft.TextStyle(
                color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
            on_change=self._on_plan_cambiado,
        )



        # ── Puerta animada ────────────────────────────────────
        self._puerta = PuertaAnimada(on_abrir=self._abrir_plan)

        # ── Layout interno ────────────────────────────────────
        fila_grado = ft.Row(
            controls=[
                ft.Text("Grado:", size=13, weight=ft.FontWeight.W_600,
                        color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
                        width=55),
                self._dd_grado,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        fila_plan = ft.Row(
            controls=[
                ft.Text("Plan:", size=13, weight=ft.FontWeight.W_600,
                        color=Colores.TEXTO, font_family=Fuentes.CAMPOS,
                        width=55),
                self._dd_plan,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        # Imagen/logo institucional a la izquierda dentro del contenedor
        logo = ft.Image(
            src="logo_miidt.jpeg",
            width=280,
            fit=ft.ImageFit.CONTAIN,
            filter_quality=ft.FilterQuality.HIGH,
            opacity=0.5
        )

        # Columna izquierda: logo
        col_logo = ft.Container(
            content=logo,
            alignment=ft.alignment.center_left,
            expand=True
        )

        # Columna derecha: dropdowns + puerta
        col_derecha = ft.Column(
            controls=[
                ft.Container(height=20),
                fila_grado,
                ft.Container(height=10),
                fila_plan,
                ft.Container(height=20),
                ft.Container(
                    content=self._puerta,
                    margin=ft.margin.only(left=250),
                ),
                ft.Container(height=30),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        contenido = ft.Row(
            controls=[ col_derecha, col_logo],
            spacing=0,
            expand=True,
        )

        super().__init__(
            content=contenido,
            bgcolor=Colores.BLANCO,
            border=ft.border.all(1.5, Colores.BORDE),
            border_radius=9,
            padding=ft.padding.symmetric(horizontal=40, vertical=120),
            margin=ft.margin.symmetric(horizontal=20, vertical=10),
            expand=True,
        )

    # ── Ciclo de vida ─────────────────────────────────────────

    def cargar_niveles(self) -> None:
        """Llama al service y rellena el dropdown de grados desde la BD."""
        niveles = self._service.obtener_niveles()
        self._dd_grado.options = [
            self._opcion(str(n.id), n.nombre) for n in niveles
        ]
        self._dd_grado.value = None
        self._dd_plan.options = []
        self._dd_plan.value   = None
        self._dd_plan.disabled = True
        self._plan_actual = None
        self._puerta.resetear()
        if self.page:
            self._dd_grado.update()
            self._dd_plan.update()

    # ── Callbacks de dropdowns ────────────────────────────────

    def _on_grado_cambiado(self, _) -> None:
        id_nivel = self._dd_grado.value
        if not id_nivel:
            return
        planes = self._service.obtener_planes_por_nivel(int(id_nivel))
        self._dd_plan.options  = [
            self._opcion(str(p.id), p.nombre) for p in planes
        ]
        self._dd_plan.value    = None
        self._dd_plan.disabled = len(planes) == 0
        self._plan_actual = None
        self._puerta.resetear()
        if self.page:
            self._dd_plan.update()

    def _on_plan_cambiado(self, _) -> None:
        val = self._dd_plan.value
        if not val:
            self._plan_actual = None
            return
        # Buscar el PlanDTO en las opciones actuales
        id_plan  = int(val)
        id_nivel = int(self._dd_grado.value)
        planes   = self._service.obtener_planes_por_nivel(id_nivel)
        self._plan_actual = next((p for p in planes if p.id == id_plan), None)
        self._puerta.resetear()

    # ── Apertura de puerta ────────────────────────────────────

    def _abrir_plan(self) -> None:
        """Se llama cuando la animación de la puerta termina."""
        if self._plan_actual is None:
            self._puerta.resetear()
            return
        self._on_abrir_plan(self._plan_actual)

    # ── Helper ────────────────────────────────────────────────

    @staticmethod
    def _opcion(key: str, text: str) -> ft.dropdown.Option:
        return ft.dropdown.Option(
            key=key, text=text,
            text_style=ft.TextStyle(
                color="#000000", font_family=Fuentes.CAMPOS),
        )


# ─────────────────────────────────────────────────────────────
# Vista principal con tabs
# ─────────────────────────────────────────────────────────────
class PlanesView(ft.Column):
    """Vista raíz: cabecera + barra de tabs + panel de contenido.

    Tabs disponibles:
    • Planes de estudios → PanelPlanesEstudios (BD real)
    • Crear plan         → CrearPlanView (panel embebido)
    • Horario por docente → HorarioDocenteView (panel embebido)
    • Historial          → HistorialView (panel embebido)

    Parámetros
    ──────────
    on_cerrar        : cierra la aplicación
    on_abrir_plan    : recibe PlanDTO cuando el usuario abre la puerta
    plan_service     : servicio para crear planes (pestaña Crear plan)
    """

    def __init__(
        self,
        page: ft.Page,
        service: PlanesService,
        on_cerrar: Callable,
        on_abrir_plan: Callable[[PlanDTO], None],
        horario_service: HorarioService | None = None,
        plan_service: PlanEstudiosService | None = None,
        on_abrir_plan_por_id: Callable[[int, int], None] | None = None,
        get_ruta_membrete: Callable[[], str | None] | None = None,
    ) -> None:
        self._page              = page
        self._service           = service
        self._on_abrir_plan     = on_abrir_plan
        self._horario_svc       = horario_service
        self._plan_svc          = plan_service
        self._on_abrir_plan_por_id = on_abrir_plan_por_id
        self._get_ruta_membrete = get_ruta_membrete

        # ── Cabecera ──────────────────────────────────────────
        self._cabecera = CabeceraApp(on_cerrar=on_cerrar)

        # ── Barra de tabs ─────────────────────────────────────
        self._tabs = BarraTabs(on_tab=self._cambiar_tab)

        # ── Paneles de contenido ──────────────────────────────
        self._panel_planes = PanelPlanesEstudios(
            page=page,
            service=service,
            on_abrir_plan=self._on_abrir_plan,
        )

        self._area_contenido = ft.Column(
            controls=[
                ft.Container(
                    content=self._panel_planes,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )

        super().__init__(
            controls=[
                self._cabecera,
                ft.Container(
                    content=self._tabs,
                    bgcolor=Colores.BLANCO,
                    padding=ft.padding.only(left=10, top=8),
                ),
                self._area_contenido,
            ],
            spacing=0,
            expand=True,
        )

    def did_mount(self) -> None:
        """Al montar la vista carga los datos desde la BD."""
        self._panel_planes.cargar_niveles()

    # ── Navegación de tabs ────────────────────────────────────

    def _cambiar_tab(self, tab: str) -> None:
        if tab == "Crear plan":
            if self._plan_svc:
                lies_lista = self._plan_svc.obtener_lies()
                lies_activa = lies_lista[0] if lies_lista else {"id": 1, "nombre": "TICs"}
                vista_crear = CrearPlanView(
                    page=self._page,
                    service=self._plan_svc,
                    lies_activa=lies_activa,
                    on_guardado=lambda: self._tabs.seleccionar_tab("Planes de estudios"),
                )
                self._area_contenido.controls = [
                    ft.Container(
                        content=vista_crear,
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                ]
                if self.page:
                    self._area_contenido.update()
        elif tab == "Planes de estudios":
            self._area_contenido.controls = [
                ft.Container(
                    content=self._panel_planes,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ]
            self._panel_planes.cargar_niveles()
            if self.page:
                self._area_contenido.update()
        elif tab == "Horario por docente":
            ruta_membrete = self._get_ruta_membrete() if self._get_ruta_membrete else None
            vista_docente = HorarioDocenteView(
                page=self._page,
                service=self._horario_svc or HorarioService(),
                ruta_membrete=ruta_membrete,
            )
            self._area_contenido.controls = [
                ft.Container(
                    content=vista_docente,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ]
            if self.page:
                self._area_contenido.update()
        elif tab == "Historial":
            ruta_membrete = self._get_ruta_membrete() if self._get_ruta_membrete else None
            vista_historial = HistorialView(
                page=self._page,
                service=self._horario_svc or HorarioService(),
                on_editar_plan=self._on_abrir_plan_por_id
                    if self._on_abrir_plan_por_id
                    else lambda _a, _b: None,
                ruta_membrete=ruta_membrete,
            )
            self._area_contenido.controls = [
                ft.Container(
                    content=vista_historial,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ]
            if self.page:
                self._area_contenido.update()
