"""
Estado centralizado de la sesión de detalle de plan.

Migrado desde: ui/views/horario_state.py (HorarioStateManager)
Ahora vive en: application/state/detalle_plan_state.py

Responsabilidades:
- IDs de horarios creados/precargados en la sesión activa.
- Caché en memoria de horas de tronco común por semestre.
- Caché de horas de optativas por LIES.
- Estado de edición (qué horario se está editando).
- Validación de colisiones horarias (delegada a HorarioValidator).
- Reconstrucción de cachés desde BD.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: lógica de renderizado aquí.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from domain.entities.horario import Horario
from domain.exceptions.horario_exceptions import HorarioConflictException
from domain.rules.horario_validator import HorarioValidator

if TYPE_CHECKING:
    from application.services.horario_service import HorarioService
    from application.dto.horario_dto import FilaHorarioDTO


class DetallePlanState:
    """Centraliza el estado mutable de la sesión de horarios.

    Esta clase es el reemplazo directo de HorarioStateManager
    (que vivía incorrectamente en ui/views/).

    Diferencias respecto al original:
    - validar_horario() ahora delega a HorarioValidator (dominio).
    - Los cachés se convierten progresivamente a entidades Horario.
    - Conserva retrocompatibilidad total con la API original para
      no romper DetallePlanView durante la transición.
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
        self._validator = HorarioValidator()

        self.id_lies_activa: int = id_lies_activa
        self.editando_id: int | None = None
        self.ids_sesion: set[int] = set()

        # ── Catálogos en memoria ──────────────────────────────
        self.aulas: list = []
        self.docentes: list = []
        self.unidades: list = []

        # Caché de tronco: {id_semestre: {id_materia: [{"dia","hora_inicio","hora_fin",...}]}}
        self.tronco_horas: dict[int, dict[int, list[dict]]] = {}

        # Caché de optativas: {id_lies: {id_sem: [{"dia","hora_inicio","hora_fin","id_horario"}]}}
        self.optativa_horas: dict[int, dict[int, list[dict]]] = {}

    # ── Sesión ────────────────────────────────────────────────

    def limpiar_sesion(self) -> None:
        """Limpia solo los IDs de sesión (al cambiar LIES)."""
        self.ids_sesion = set()

    def limpiar_todo(self) -> None:
        """Limpia IDs, cachés y estado de edición (al cambiar semestre)."""
        self.ids_sesion = set()
        self.tronco_horas = {}
        self.optativa_horas = {}

    def limpiar_completo(self) -> None:
        """Limpia absolutamente todo (al volver / salir)."""
        self.editando_id = None
        self.ids_sesion = set()
        self.tronco_horas = {}
        self.optativa_horas = {}

    # ── Caché de tronco ───────────────────────────────────────

    def registrar_tronco(
        self,
        id_sem: int,
        id_materia: int,
        filas: list,
        id_lies: int | None = None,
        id_aula: int | None = None,
        id_docente: int | None = None,
    ) -> None:
        """Agrega horas al caché de tronco, evitando duplicados."""
        if id_sem not in self.tronco_horas:
            self.tronco_horas[id_sem] = {}
        if id_materia not in self.tronco_horas[id_sem]:
            self.tronco_horas[id_sem][id_materia] = []
        existing = {
            (h["dia"], h["hora_inicio"], h["hora_fin"])
            for h in self.tronco_horas[id_sem][id_materia]
        }
        for f in filas:
            d = self._fila_to_dict(f)
            if id_lies is not None:
                d["id_lies"] = id_lies
            if id_aula is not None:
                d["id_aula"] = id_aula
            if id_docente is not None:
                d["id_docente"] = id_docente
            key = (d["dia"], d["hora_inicio"], d["hora_fin"])
            if key not in existing:
                self.tronco_horas[id_sem][id_materia].append(d)
                existing.add(key)

    # ── Caché de optativas ────────────────────────────────────

    def registrar_optativa(
        self, id_lies: int, id_sem: int, filas: list, id_horario: int,
    ) -> None:
        """Registra las horas de una optativa en el caché."""
        if id_lies not in self.optativa_horas:
            self.optativa_horas[id_lies] = {}
        if id_sem not in self.optativa_horas[id_lies]:
            self.optativa_horas[id_lies][id_sem] = []
        for f in filas:
            d = self._fila_to_dict(f)
            d["id_horario"] = id_horario
            self.optativa_horas[id_lies][id_sem].append(d)

    def actualizar_optativa(
        self, id_lies: int, id_sem: int, filas: list, id_horario: int,
    ) -> None:
        """Reemplaza las horas de una optativa editada en el caché."""
        if id_lies in self.optativa_horas and id_sem in self.optativa_horas[id_lies]:
            self.optativa_horas[id_lies][id_sem] = [
                h for h in self.optativa_horas[id_lies][id_sem]
                if h.get("id_horario") != id_horario
            ]
        self.registrar_optativa(id_lies, id_sem, filas, id_horario)

    def quitar_optativa(self, id_lies: int, id_sem: int, id_horario: int) -> None:
        """Elimina las horas de una optativa del caché al borrarla."""
        if id_lies in self.optativa_horas and id_sem in self.optativa_horas[id_lies]:
            self.optativa_horas[id_lies][id_sem] = [
                h for h in self.optativa_horas[id_lies][id_sem]
                if h.get("id_horario") != id_horario
            ]

    # ── Validación (ahora usa HorarioValidator del dominio) ───

    def validar_horario(
        self,
        es_tronco: bool,
        id_materia: int | None,
        id_sem: int | None,
        filas: list,
        id_horario_excluir: int | None = None,
        id_aula: int | None = None,
        id_docente: int | None = None,
    ) -> str | None:
        """Valida reglas de horario. Retorna mensaje de error o None.

        Mantiene la firma original de HorarioStateManager para
        retrocompatibilidad con DetallePlanView durante la transición.

        Internamente delega a HorarioValidator (dominio) convirtiendo
        los dicts del caché a objetos Horario.
        """
        if id_sem is None:
            return None

        # Construir lista de Horario existentes desde los cachés
        existentes = self._cachés_a_horarios(id_sem, id_horario_excluir)

        # Construir los Horario nuevos desde las filas del formulario
        nuevos = self._filas_a_horarios(
            filas, es_tronco, id_materia, id_sem,
            id_aula, id_docente,
        )

        # Validar cada fila nueva contra los existentes
        for nuevo in nuevos:
            try:
                self._validator.validar_traslapes(
                    nuevo, existentes, id_horario_excluir=id_horario_excluir
                )
            except HorarioConflictException as exc:
                return str(exc)

        return None

    # ── Reconstrucción de cachés ──────────────────────────────

    def reconstruir_caches(self, id_sem_str: str | None) -> None:
        """Limpia y reconstruye los cachés desde los horarios de la sesión."""
        self.tronco_horas = {}
        self.optativa_horas = {}
        if not self.ids_sesion or not id_sem_str:
            return

        id_sem = int(id_sem_str)
        todos = self._service.obtener_horarios_filtrados(
            id_plan=self._id_plan,
            id_lies=self.id_lies_activa,
            id_semestre=id_sem,
            id_semestre_opt=self._sem_opt_id,
        )
        registros = [r for r in todos if r.id_horario in self.ids_sesion]

        for r in registros:
            filas = [{"dia": r.dia, "hora_inicio": r.hora_inicio, "hora_fin": r.hora_fin}]
            detalle = self._service.obtener_horario_detalle(r.id_horario)
            if detalle is None:
                continue
            id_materia = self._service.obtener_id_materia(detalle.id_asignacion)
            if id_materia is not None:
                self.registrar_tronco(id_sem, id_materia, filas)
            else:
                self.registrar_optativa(self.id_lies_activa, id_sem, filas, r.id_horario)

    # ── Helpers privados ──────────────────────────────────────

    def _cachés_a_horarios(
        self, id_sem: int, id_horario_excluir: int | None
    ) -> list[Horario]:
        """Convierte los cachés de dicts a objetos Horario para el validator."""
        horarios: list[Horario] = []
        sem_cache = self.tronco_horas.get(id_sem, {})

        # Tronco
        for id_materia, filas in sem_cache.items():
            for f in filas:
                try:
                    h = Horario(
                        dia=f["dia"],
                        hora_inicio=f["hora_inicio"],
                        hora_fin=f["hora_fin"],
                        id_asignacion=0,  # no disponible en caché
                        id_docente=f.get("id_docente", 0),
                        id_aula=f.get("id_aula", 0),
                        id_periodo=0,
                        id_semestre=id_sem,
                        id_lies=f.get("id_lies"),
                        id_materia=id_materia,
                    )
                    horarios.append(h)
                except Exception:
                    pass

        # Optativas de la LIES activa
        lies_opt = self.optativa_horas.get(self.id_lies_activa, {})
        for f in lies_opt.get(id_sem, []):
            if f.get("id_horario") == id_horario_excluir:
                continue
            try:
                h = Horario(
                    dia=f["dia"],
                    hora_inicio=f["hora_inicio"],
                    hora_fin=f["hora_fin"],
                    id_asignacion=0,
                    id_docente=0,
                    id_aula=0,
                    id_periodo=0,
                    id_semestre=id_sem,
                    id_lies=self.id_lies_activa,
                    id_materia=None,
                    id_horario=f.get("id_horario"),
                )
                horarios.append(h)
            except Exception:
                pass

        return horarios

    def _filas_a_horarios(
        self,
        filas: list,
        es_tronco: bool,
        id_materia: int | None,
        id_sem: int,
        id_aula: int | None,
        id_docente: int | None,
    ) -> list[Horario]:
        """Convierte las filas del formulario a objetos Horario."""
        result = []
        for f in filas:
            d = self._fila_to_dict(f)
            try:
                h = Horario(
                    dia=d["dia"],
                    hora_inicio=d["hora_inicio"],
                    hora_fin=d["hora_fin"],
                    id_asignacion=0,
                    id_docente=id_docente or 0,
                    id_aula=id_aula or 0,
                    id_periodo=0,
                    id_semestre=id_sem,
                    id_lies=self.id_lies_activa,
                    id_materia=id_materia if es_tronco else None,
                )
                result.append(h)
            except Exception:
                pass
        return result

    @staticmethod
    def _fila_to_dict(f) -> dict:
        """Convierte FilaHorarioDTO o dict a dict estándar."""
        if isinstance(f, dict):
            return f
        d = {"dia": f.dia, "hora_inicio": f.hora_inicio, "hora_fin": f.hora_fin}
        for k in ("id_lies", "id_aula", "id_docente"):
            if hasattr(f, k):
                d[k] = getattr(f, k)
        return d
