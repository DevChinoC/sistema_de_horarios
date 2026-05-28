"""
Estado centralizado de la sesión de detalle de plan.

Responsabilidades (solo estado de UI):
- Estado de edición (qué horario se está editando).
- Catálogos en memoria (aulas, docentes, unidades).
- LIES activa e id_plan.
- ids_sesion_por_contexto: sesiones aisladas por (id_lies, id_semestre).
  Cada contexto tiene su propio set de IDs de horarios creados.

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
    - ids_sesion_por_contexto: dict[(id_lies, id_semestre)] → set[int]
      Aísla horarios creados por cada combinación LIES+semestre.
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

        # Sesiones aisladas por contexto (id_lies, id_semestre)
        self.ids_sesion_por_contexto: dict[tuple[int | None, int | None], set[int]] = {}

        # ── Catálogos en memoria ──────────────────────────────
        self.aulas: list = []
        self.docentes: list = []
        self.unidades: list = []

    # ── Sesión por contexto ───────────────────────────────────

    def obtener_ids_contexto(self, ctx: tuple[int | None, int | None]) -> set[int]:
        """Retorna los IDs de sesión para un contexto dado."""
        return self.ids_sesion_por_contexto.get(ctx, set())

    def agregar_id(self, ctx: tuple[int | None, int | None], id_horario: int) -> None:
        """Registra un ID de horario en el contexto dado."""
        if ctx not in self.ids_sesion_por_contexto:
            self.ids_sesion_por_contexto[ctx] = set()
        self.ids_sesion_por_contexto[ctx].add(id_horario)

    def descartar_id(self, ctx: tuple[int | None, int | None], id_horario: int) -> None:
        """Elimina un ID de horario del contexto dado."""
        ids = self.ids_sesion_por_contexto.get(ctx)
        if ids:
            ids.discard(id_horario)

    # ── Limpieza ──────────────────────────────────────────────

    def limpiar_sesion(self) -> None:
        """Limpia solo los IDs de sesión (al cambiar LIES)."""
        # NO limpiar — cada contexto se preserva independientemente
        pass

    def limpiar_todo(self) -> None:
        """Limpia IDs y estado de edición (al cambiar semestre).

        Ya no hay cachés de validación — la BD es la fuente de verdad.
        """
        # NO limpiar por contexto — solo resetear edición
        pass

    def limpiar_completo(self) -> None:
        """Limpia absolutamente todo (al volver / salir)."""
        self.editando_id_detalle = None
        self.ids_sesion_por_contexto.clear()
