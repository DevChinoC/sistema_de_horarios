"""Gestión centralizada de estado para la sesión de horarios.

Encapsula:
- IDs de horarios creados en la sesión actual
- Caché en memoria de horas de tronco común por semestre
- Caché de horas de optativas por LIES
- Estado de edición
- Validación de colisiones horarias
- Reconstrucción de cachés desde BD
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from application.dto.horario_dto import FilaHorarioDTO

if TYPE_CHECKING:
    from application.services.horario_service import HorarioService


class HorarioStateManager:
    """Centraliza el estado mutable de la sesión de horarios.

    Responsabilidades:
    - Mantener los IDs de horarios creados/precargados en la sesión
    - Gestionar los cachés de tronco y optativas para validación rápida
    - Validar reglas de negocio de colisiones entre horarios
    - Reconstruir cachés desde BD cuando sea necesario
    """

    def __init__(
        self,
        service: HorarioService,
        id_plan: int,
        id_lies_activa: int,
        sem_opt_id: int | None,
    ) -> None:
        self._service = service
        self._id_plan = id_plan
        self._sem_opt_id = sem_opt_id

        self.id_lies_activa: int = id_lies_activa
        self.editando_id: int | None = None
        self.ids_sesion: set[int] = set()

        # Caché: {id_semestre: {id_materia: [{"dia", "hora_inicio", "hora_fin"}, ...]}}
        self.tronco_horas: dict[int, dict[int, list[dict]]] = {}

        # Caché: {id_lies: {id_sem: [{"dia", "hora_inicio", "hora_fin", "id_horario"}, ...]}}
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
        self, id_sem: int, id_materia: int, filas: list,
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

    # ── Validación de horarios ────────────────────────────────

    def validar_horario(
        self,
        es_tronco: bool,
        id_materia: int | None,
        id_sem: int | None,
        filas: list,
        id_horario_excluir: int | None = None,
    ) -> str | None:
        """Valida reglas de horario.  Retorna mensaje de error o None.

        Reglas:
        1. Misma materia de tronco en otra LIES → mismos días y horas.
        2. Diferente materia de tronco → no puede solaparse en mismo día.
        3. Optativa → no puede solaparse con tronco común en mismo día.
        4. Optativas dentro de la misma LIES → no pueden solaparse en mismo día.
        5. Todo es por semestre; otro semestre no afecta.
        """
        if id_sem is None:
            return None
        sem_cache = self.tronco_horas.get(id_sem, {})
        filas_d = [self._fila_to_dict(f) for f in filas]

        if es_tronco and id_materia is not None:
            # ── Regla: otra materia de tronco → sin solapamiento (por día)
            for mat_id, mat_hrs in sem_cache.items():
                if mat_id == id_materia:
                    continue
                for h_ex in mat_hrs:
                    hi_ex = datetime.strptime(h_ex["hora_inicio"], "%H:%M")
                    hf_ex = datetime.strptime(h_ex["hora_fin"], "%H:%M")
                    for f in filas_d:
                        if f.get("dia", "") != h_ex.get("dia", ""):
                            continue
                        hi_n = datetime.strptime(f["hora_inicio"], "%H:%M")
                        hf_n = datetime.strptime(f["hora_fin"], "%H:%M")
                        if hi_n < hf_ex and hf_n > hi_ex:
                            return (
                                f"El rango {f['dia']} {f['hora_inicio']}–{f['hora_fin']} "
                                f"colisiona con otra materia de tronco común "
                                f"({h_ex['dia']} {h_ex['hora_inicio']}–{h_ex['hora_fin']}).\n"
                                f"Las materias de tronco no pueden compartir "
                                f"rango horario en el mismo día y semestre."
                            )
        else:
            # ── Regla 3: optativa vs tronco → sin solapamiento (por día)
            for _mat_id, mat_hrs in sem_cache.items():
                for h_ex in mat_hrs:
                    hi_ex = datetime.strptime(h_ex["hora_inicio"], "%H:%M")
                    hf_ex = datetime.strptime(h_ex["hora_fin"], "%H:%M")
                    for f in filas_d:
                        if f.get("dia", "") != h_ex.get("dia", ""):
                            continue
                        hi_n = datetime.strptime(f["hora_inicio"], "%H:%M")
                        hf_n = datetime.strptime(f["hora_fin"], "%H:%M")
                        if hi_n < hf_ex and hf_n > hi_ex:
                            return (
                                f"El horario {f['dia']} {f['hora_inicio']}–{f['hora_fin']} "
                                f"colisiona con una materia de tronco común "
                                f"({h_ex['dia']} {h_ex['hora_inicio']}–{h_ex['hora_fin']}).\n"
                                f"Las optativas no pueden compartir rango "
                                f"horario con materias de tronco común en el mismo día."
                            )

            # ── Regla 4: optativa vs optativa en la MISMA LIES
            lies_opt_cache = self.optativa_horas.get(self.id_lies_activa, {})
            opt_sem_cache  = lies_opt_cache.get(id_sem, [])
            for h_ex in opt_sem_cache:
                if id_horario_excluir is not None and h_ex.get("id_horario") == id_horario_excluir:
                    continue
                hi_ex = datetime.strptime(h_ex["hora_inicio"], "%H:%M")
                hf_ex = datetime.strptime(h_ex["hora_fin"], "%H:%M")
                for f in filas_d:
                    if f.get("dia", "") != h_ex.get("dia", ""):
                        continue
                    hi_n = datetime.strptime(f["hora_inicio"], "%H:%M")
                    hf_n = datetime.strptime(f["hora_fin"], "%H:%M")
                    if hi_n < hf_ex and hf_n > hi_ex:
                        return (
                            f"El horario {f['dia']} {f['hora_inicio']}–{f['hora_fin']} "
                            f"colisiona con otra optativa en esta LIES "
                            f"({h_ex['dia']} {h_ex['hora_inicio']}–{h_ex['hora_fin']}).\n"
                            f"Dos optativas no pueden compartir el mismo horario "
                            f"en la misma LIES y semestre."
                        )
        return None

    # ── Reconstrucción de cachés ──────────────────────────────

    def reconstruir_caches(self, id_sem_str: str | None) -> None:
        """Limpia y reconstruye completamente los cachés de tronco y optativa
        a partir de los horarios actuales en la sesión."""
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
                self.registrar_optativa(
                    self.id_lies_activa, id_sem, filas, r.id_horario)

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _fila_to_dict(f) -> dict:
        """Convierte FilaHorarioDTO o dict a dict estándar."""
        if isinstance(f, dict):
            return f
        return {"dia": f.dia, "hora_inicio": f.hora_inicio, "hora_fin": f.hora_fin}
