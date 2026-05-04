"""navegador.py
Gestiona la navegación entre vistas dentro de la misma ventana.

Cambios:
- Todas las pestañas (Planes, Crear plan, Docente, Historial) se
  manejan dentro de PlanesView como paneles embebidos.
- ir_a_crear_plan / ir_a_docente / ir_a_historial crean PlanesView
  y seleccionan programáticamente la pestaña correspondiente.
"""

import flet as ft

from application.services.planes_service import PlanesService
from application.services.plan_estudios_service import PlanEstudiosService
from application.services.horario_service import HorarioService
from application.dto.planes_dto import PlanDTO

from ui.views.planes_view import PlanesView
from ui.views.detalle_plan_view import DetallePlanView


class Navegador:
    """Gestiona la navegación entre vistas dentro de la misma ventana.

    Principios POO aplicados:
    - Responsabilidad única: solo gestiona el flujo de navegación.
    - Encapsulamiento: los detalles de cada vista se ocultan aquí.
    - El membrete de cada plan vive en su propia carpeta del proyecto;
      no se almacena ninguna ruta global en este objeto.
    """

    def __init__(
        self,
        page: ft.Page,
        planes_service: PlanesService,
        plan_service: PlanEstudiosService,
        horario_service: HorarioService,
    ) -> None:
        self._page        = page
        self._planes_svc  = planes_service
        self._plan_svc    = plan_service
        self._horario_svc = horario_service

    # ── Métodos de navegación ─────────────────────────────────

    def ir_a_planes(self) -> None:
        """Vista principal: selección de grado y plan de estudios."""
        self._page.controls.clear()
        vista = PlanesView(
            page=self._page,
            service=self._planes_svc,
            on_cerrar=lambda _: self._page.window.close(),
            on_abrir_plan=self.ir_a_detalle_plan,
            horario_service=self._horario_svc,
            plan_service=self._plan_svc,
            on_abrir_plan_por_id=self.ir_a_detalle_plan_por_id,
            get_ruta_membrete=None,
        )
        self._page.add(vista)

    def ir_a_crear_plan(self) -> None:
        """Vista para crear un nuevo plan de estudios."""
        self._page.controls.clear()
        self._page.overlay.clear()
        vista = PlanesView(
            page=self._page,
            service=self._planes_svc,
            on_cerrar=lambda _: self._page.window.close(),
            on_abrir_plan=self.ir_a_detalle_plan,
            horario_service=self._horario_svc,
            plan_service=self._plan_svc,
            on_abrir_plan_por_id=self.ir_a_detalle_plan_por_id,
            get_ruta_membrete=None,
        )
        self._page.add(vista)
        # Programáticamente seleccionar la pestaña "Crear plan"
        vista._tabs.seleccionar_tab("Crear plan")

    def ir_a_docente(self) -> None:
        """Vista 'Horario por docente' — accesible desde cualquier pestaña."""
        self._page.controls.clear()
        self._page.overlay.clear()
        vista = PlanesView(
            page=self._page,
            service=self._planes_svc,
            on_cerrar=lambda _: self._page.window.close(),
            on_abrir_plan=self.ir_a_detalle_plan,
            horario_service=self._horario_svc,
            plan_service=self._plan_svc,
            on_abrir_plan_por_id=self.ir_a_detalle_plan_por_id,
            get_ruta_membrete=None,
        )
        self._page.add(vista)
        # Programáticamente seleccionar la pestaña "Horario por docente"
        vista._tabs.seleccionar_tab("Horario por docente")

    def ir_a_historial(self) -> None:
        """Vista 'Historial' — accesible desde cualquier pestaña."""
        self._page.controls.clear()
        self._page.overlay.clear()
        vista = PlanesView(
            page=self._page,
            service=self._planes_svc,
            on_cerrar=lambda _: self._page.window.close(),
            on_abrir_plan=self.ir_a_detalle_plan,
            horario_service=self._horario_svc,
            plan_service=self._plan_svc,
            on_abrir_plan_por_id=self.ir_a_detalle_plan_por_id,
            get_ruta_membrete=None,
        )
        self._page.add(vista)
        # Programáticamente seleccionar la pestaña "Historial"
        vista._tabs.seleccionar_tab("Historial")

    def ir_a_detalle_plan(self, plan: PlanDTO) -> None:
        """Vista de detalle y asignación de horarios de un plan."""
        self._limpiar_y_abrir_detalle(plan.id)

    def ir_a_detalle_plan_por_id(self, id_plan: int, id_plan_generado: int | None = None) -> None:
        """Navega a DetallePlanView usando directamente un id_plan.
        Si se pasa id_plan_generado, precarga los horarios de ese plan generado.
        """
        self._limpiar_y_abrir_detalle(id_plan, id_plan_generado)

    # ── Helpers privados ─────────────────────────────────────

    def _limpiar_y_abrir_detalle(self, id_plan: int, id_plan_generado: int | None = None) -> None:
        self._page.controls.clear()
        self._page.overlay.clear()
        vista = DetallePlanView(
            page=self._page,
            id_plan=id_plan,
            service=self._horario_svc,
            on_volver=self.ir_a_planes,
            ruta_membrete=None,  # se resuelve internamente por HorarioService
            id_plan_generado=id_plan_generado,
        )
        self._page.add(vista)
