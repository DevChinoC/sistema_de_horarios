import flet as ft

from application.services.planes_service import PlanesService
from application.services.plan_estudios_service import PlanEstudiosService
from application.services.horario_service import HorarioService
from application.dto.planes_dto import PlanDTO

from ui.views.planes_view import PlanesView
from ui.views.crear_plan_view import CrearPlanView
from ui.views.detalle_plan_view import DetallePlanView


class Navegador:
    """Gestiona la navegación entre vistas dentro de la misma ventana.

    Todas las vistas comparten la misma ft.Page — no se abren ventanas
    nuevas. Cada método limpia los controles actuales y agrega la vista
    correspondiente.
    """

    def __init__(
        self,
        page: ft.Page,
        planes_service: PlanesService,
        plan_service: PlanEstudiosService,
        horario_service: HorarioService,
    ) -> None:
        self._page           = page
        self._planes_svc     = planes_service
        self._plan_svc       = plan_service
        self._horario_svc    = horario_service
        self._ruta_membrete: str | None = None

    # ── Membrete global ───────────────────────────────────────

    @property
    def ruta_membrete(self) -> str | None:
        return self._ruta_membrete

    @ruta_membrete.setter
    def ruta_membrete(self, valor: str | None) -> None:
        self._ruta_membrete = valor

    # ── Métodos de navegación ─────────────────────────────────


    def ir_a_planes(self) -> None:
        """Vista principal: selección de grado y plan de estudios."""
        self._page.controls.clear()
        vista = PlanesView(
            page=self._page,
            service=self._planes_svc,
            on_cerrar=lambda _: self._page.window.close(),
            on_ir_crear_plan=self.ir_a_crear_plan,
            on_abrir_plan=self.ir_a_detalle_plan,
            horario_service=self._horario_svc,
            on_abrir_plan_por_id=self.ir_a_detalle_plan_por_id,
            get_ruta_membrete=lambda: self._ruta_membrete,
        )
        self._page.add(vista)

    def ir_a_crear_plan(self) -> None:
        """Vista para crear un nuevo plan de estudios."""
        self._page.controls.clear()
        lies_lista  = self._plan_svc.obtener_lies()
        lies_activa = lies_lista[0] if lies_lista else {"id": 1, "nombre": "TICs"}
        vista = CrearPlanView(
            page=self._page,
            service=self._plan_svc,
            lies_activa=lies_activa,
            on_guardado=self.ir_a_planes,
            on_cancelado=self.ir_a_planes,
            on_membrete_seleccionado=self._set_membrete,
        )
        self._page.add(vista)

    def _set_membrete(self, ruta: str | None) -> None:
        """Callback invocado por CrearPlanView al seleccionar membrete."""
        self._ruta_membrete = ruta

    def ir_a_detalle_plan(self, plan: PlanDTO) -> None:
        """Vista de detalle y asignación de horarios de un plan."""
        self._page.controls.clear()
        # Limpiar FilePickers residuales del overlay
        self._page.overlay.clear()
        vista = DetallePlanView(
            page=self._page,
            id_plan=plan.id,
            service=self._horario_svc,
            on_volver=self.ir_a_planes,
            ruta_membrete=self._ruta_membrete,
        )
        self._page.add(vista)

    def ir_a_detalle_plan_por_id(self, id_plan: int) -> None:
        """Navega a DetallePlanView usando directamente un id_plan (desde historial)."""
        self._page.controls.clear()
        # Limpiar FilePickers residuales del overlay
        self._page.overlay.clear()
        vista = DetallePlanView(
            page=self._page,
            id_plan=id_plan,
            service=self._horario_svc,
            on_volver=self.ir_a_planes,
            ruta_membrete=self._ruta_membrete,
        )
        self._page.add(vista)

