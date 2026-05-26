"""
Estado centralizado de la sesión de detalle de plan.

Responsabilidades (solo estado de UI):
- Estado de edición (qué horario se está editando).
- Catálogos en memoria (aulas, docentes, unidades).
- LIES activa e id_plan.
- ids_sesion: estado AUXILIAR opcional (NO fuente de verdad).
  La fuente de verdad para visualización es SIEMPRE la BD.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: lógica de renderizado aquí.
PROHIBIDO: validación de reglas de negocio aquí.
    → Toda validación se hace en el backend via HorarioValidator + BD real.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.services.horario_service import HorarioService


class DetallePlanState:
    """Centraliza el estado mutable de la sesión de horarios.

    Solo almacena estado de UI:
    - ids_sesion: estado auxiliar opcional (NO fuente de verdad).
      La visualización (tabla, preview, PDF) consulta la BD directamente.
    - editando_id_detalle: ID del detalle que se está editando.
    - Catálogos: aulas, docentes, unidades.

    La validación de reglas de negocio se hace en el backend
    (HorarioService → CrearHorarioUseCase → HorarioValidator → BD real).
    """

    def __init__(
        self,
        service: "HorarioService",
        id_plan: int,
        id_lies_activa: int,
        sem_opt_id: int | None,
    ) -> None:
        self._service = service
        self._id_plan = id_plan
        self._sem_opt_id = sem_opt_id

        self.id_lies_activa: int = id_lies_activa
        self.editando_id_detalle: int | None = None
        self.ids_sesion: set[int] = set()

        # ── Catálogos en memoria ──────────────────────────────
        self.aulas: list = []
        self.docentes: list = []
        self.unidades: list = []

    # ── Sesión ────────────────────────────────────────────────

    def limpiar_sesion(self) -> None:
        """Limpia solo los IDs de sesión (al cambiar LIES)."""
        self.ids_sesion = set()

    def limpiar_todo(self) -> None:
        """Limpia IDs y estado de edición (al cambiar semestre).

        Ya no hay cachés de validación — la BD es la fuente de verdad.
        """
        self.ids_sesion = set()

    def limpiar_completo(self) -> None:
        """Limpia absolutamente todo (al volver / salir)."""
        self.editando_id_detalle = None
        self.ids_sesion = set()
