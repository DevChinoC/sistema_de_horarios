"""
Reglas de negocio para validación de horarios.

Extrae la lógica de validación que actualmente vive en:
- HorarioStateManager.validar_horario() (ui/views/horario_state.py)
- DetallePlanView._agregar() (ui/views/detalle_plan_view.py)

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from domain.exceptions.horario_exceptions import HorarioConflictException

if TYPE_CHECKING:
    from domain.entities.horario import Horario


class HorarioValidator:
    """Valida las reglas de negocio de los horarios.

    Reglas implementadas:
    1. Misma materia de tronco en otra LIES → debe coincidir exactamente
       en día, hora, aula y docente.
    2. Diferente materia de tronco → no puede solaparse en mismo día/semestre.
    3. Optativa vs tronco → no puede solaparse en mismo día/semestre.
    4. Optativa vs optativa en la misma LIES → no puede solaparse.
    """

    # ── API principal ─────────────────────────────────────────

    def validar_traslapes(
        self,
        nuevo: "Horario",
        existentes: list["Horario"],
        id_horario_excluir: int | None = None,
    ) -> None:
        """Valida que el nuevo horario no traslape con los existentes.

        Aplica todas las reglas de negocio en orden.

        Args:
            nuevo: El horario que se quiere agregar/editar.
            existentes: Lista de horarios ya registrados en la misma sesión.
            id_horario_excluir: ID de un horario a excluir de la validación
                (usado al editar para no validar contra sí mismo).

        Raises:
            HorarioConflictException: Si se viola alguna regla de negocio.
        """
        candidatos = [
            h for h in existentes
            if id_horario_excluir is None or h.id_horario != id_horario_excluir
        ]

        if nuevo.es_tronco_comun():
            self._validar_tronco_cross_lies(nuevo, candidatos)
            self._validar_tronco_vs_tronco(nuevo, candidatos)
        else:
            self._validar_optativa_vs_tronco(nuevo, candidatos)
            self._validar_optativa_vs_optativa(nuevo, candidatos)

    def validar_tronco_cross_lies(
        self,
        nuevo: "Horario",
        existentes_cross_lies: list["Horario"],
    ) -> None:
        """Valida que el tronco común sea idéntico entre LIES.

        Uso: cuando la materia ya fue asignada en otra LIES, el nuevo
        registro debe coincidir en día, hora, aula y docente.

        Args:
            nuevo: Horario nuevo a agregar.
            existentes_cross_lies: Horarios de la misma materia en OTRAS lies.

        Raises:
            HorarioConflictException: Si no coincide exactamente.
        """
        self._validar_tronco_cross_lies(nuevo, existentes_cross_lies)

    def validar_optativa_vs_tronco(
        self,
        optativa: "Horario",
        troncos: list["Horario"],
    ) -> None:
        """Valida que una optativa no colisione con materias de tronco.

        Raises:
            HorarioConflictException: Si hay colisión.
        """
        self._validar_optativa_vs_tronco(optativa, troncos)

    def validar_optativa_vs_optativa(
        self,
        nueva: "Horario",
        existentes: list["Horario"],
    ) -> None:
        """Valida que dos optativas de la misma LIES no colisionen.

        Raises:
            HorarioConflictException: Si hay colisión.
        """
        self._validar_optativa_vs_optativa(nueva, existentes)

    # ── Implementaciones privadas ─────────────────────────────

    def _validar_tronco_cross_lies(
        self,
        nuevo: "Horario",
        existentes: list["Horario"],
    ) -> None:
        """Regla 1: misma materia en otra LIES → exigir igualdad exacta."""
        cross = [
            h for h in existentes
            if (h.es_tronco_comun()
                and h.id_materia == nuevo.id_materia
                and h.id_lies is not None
                and nuevo.id_lies is not None
                and h.id_lies != nuevo.id_lies)
        ]
        if not cross:
            return

        for h_ex in cross:
            if not nuevo.mismo_rango_que(h_ex):
                raise HorarioConflictException(
                    mensaje=(
                        "Esta materia de tronco común ya fue asignada en otra "
                        "LIES con diferente horario.\n"
                        "Debe coincidir en día, hora, aula y docente."
                    ),
                    conflictos=[{
                        "dia": str(h_ex.dia),
                        "hora_inicio": str(h_ex.hora_inicio),
                        "hora_fin": str(h_ex.hora_fin),
                    }],
                )
            if nuevo.id_aula != h_ex.id_aula:
                raise HorarioConflictException(
                    mensaje=(
                        "Esta materia de tronco común ya fue asignada en otra "
                        "LIES con un aula diferente.\n"
                        "Debe coincidir en día, hora, aula y docente."
                    ),
                )
            if nuevo.id_docente != h_ex.id_docente:
                raise HorarioConflictException(
                    mensaje=(
                        "Esta materia de tronco común ya fue asignada en otra "
                        "LIES con un docente diferente.\n"
                        "Debe coincidir en día, hora, aula y docente."
                    ),
                )

    def _validar_tronco_vs_tronco(
        self,
        nuevo: "Horario",
        existentes: list["Horario"],
    ) -> None:
        """Regla 2: otra materia de tronco → sin solapamiento."""
        otros_troncos = [
            h for h in existentes
            if h.es_tronco_comun() and h.id_materia != nuevo.id_materia
        ]
        for h_ex in otros_troncos:
            if nuevo.traslapa(h_ex):
                raise HorarioConflictException(
                    mensaje=(
                        f"El rango {nuevo.dia} {nuevo.hora_inicio}–{nuevo.hora_fin} "
                        f"colisiona con otra materia de tronco común "
                        f"({h_ex.dia} {h_ex.hora_inicio}–{h_ex.hora_fin}).\n"
                        f"Las materias de tronco no pueden compartir "
                        f"rango horario en el mismo día y semestre."
                    ),
                    conflictos=[{
                        "dia": str(h_ex.dia),
                        "hora_inicio": str(h_ex.hora_inicio),
                        "hora_fin": str(h_ex.hora_fin),
                    }],
                )

    def _validar_optativa_vs_tronco(
        self,
        optativa: "Horario",
        existentes: list["Horario"],
    ) -> None:
        """Regla 3: optativa vs tronco → sin solapamiento."""
        troncos = [h for h in existentes if h.es_tronco_comun()]
        for h_ex in troncos:
            if optativa.traslapa(h_ex):
                raise HorarioConflictException(
                    mensaje=(
                        f"El horario {optativa.dia} "
                        f"{optativa.hora_inicio}–{optativa.hora_fin} "
                        f"colisiona con una materia de tronco común "
                        f"({h_ex.dia} {h_ex.hora_inicio}–{h_ex.hora_fin}).\n"
                        f"Las optativas no pueden compartir rango horario "
                        f"con materias de tronco común en el mismo día."
                    ),
                    conflictos=[{
                        "dia": str(h_ex.dia),
                        "hora_inicio": str(h_ex.hora_inicio),
                        "hora_fin": str(h_ex.hora_fin),
                    }],
                )

    def _validar_optativa_vs_optativa(
        self,
        nueva: "Horario",
        existentes: list["Horario"],
    ) -> None:
        """Regla 4: optativa vs optativa en la misma LIES → sin solapamiento."""
        otras_optativas = [
            h for h in existentes
            if (not h.es_tronco_comun()
                and h.id_lies == nueva.id_lies)
        ]
        for h_ex in otras_optativas:
            if nueva.traslapa(h_ex):
                raise HorarioConflictException(
                    mensaje=(
                        f"El horario {nueva.dia} "
                        f"{nueva.hora_inicio}–{nueva.hora_fin} "
                        f"colisiona con otra optativa en esta LIES "
                        f"({h_ex.dia} {h_ex.hora_inicio}–{h_ex.hora_fin}).\n"
                        f"Dos optativas no pueden compartir el mismo horario "
                        f"en la misma LIES y semestre."
                    ),
                    conflictos=[{
                        "dia": str(h_ex.dia),
                        "hora_inicio": str(h_ex.hora_inicio),
                        "hora_fin": str(h_ex.hora_fin),
                    }],
                )
