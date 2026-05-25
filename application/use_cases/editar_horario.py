"""
Caso de uso: Editar Horario

Responsabilidad única: orquestar la actualización de un horario existente.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a BD directamente aquí.
"""
from __future__ import annotations

from datetime import datetime

from application.dto.horario_dto import GuardarHorarioDTO
from application.interfaces.horario_repository_interface import IHorarioRepository
from domain.entities.horario import Horario
from domain.exceptions.horario_exceptions import HorarioInvalidoException
from domain.rules.horario_validator import HorarioValidator


class EditarHorarioUseCase:
    """Orquesta la edición de un horario existente.

    Flujo:
        1. Construir la entidad Horario actualizada (valida invariantes).
        2. Validar conflictos excluyendo el propio horario editado.
        3. Persistir los cambios mediante el repositorio.

    Raises:
        HorarioInvalidoException: Si los datos del horario son inválidos.
        HorarioConflictException: Si hay conflicto con otros horarios.
    """

    def __init__(
        self,
        repo: IHorarioRepository,
        validator: HorarioValidator,
    ) -> None:
        self._repo = repo
        self._validator = validator

    def ejecutar(
        self,
        id_horario: int,
        dto: GuardarHorarioDTO,
        horarios_existentes: list[Horario] | None = None,
    ) -> None:
        """Actualiza un horario existente.

        Args:
            id_horario: ID del horario a actualizar.
            dto: Nuevos datos del horario.
            horarios_existentes: Lista de Horarios en sesión para validar
                conflictos. El propio horario editado se excluye automáticamente.

        Raises:
            HorarioInvalidoException: Datos inválidos.
            HorarioConflictException: Conflicto de horario.
        """
        # 1. Construir entidad actualizada (valida hora_inicio < hora_fin)
        actualizado = Horario(
            dia=dto.dia,
            hora_inicio=dto.hora_inicio,
            hora_fin=dto.hora_fin,
            id_asignacion=dto.id_asignacion,
            id_docente=dto.id_docente,
            id_aula=dto.id_aula,
            id_periodo=dto.id_periodo,
            id_semestre=dto.id_semestre,
            id_lies=dto.id_lies,
            id_materia=self._repo.obtener_id_materia(dto.id_asignacion),
            id_horario=id_horario,
            total_horas=dto.total_horas,
        )

        # 2. Validar conflictos (excluir el horario que estamos editando)
        if horarios_existentes:
            self._validator.validar_traslapes(
                actualizado,
                horarios_existentes,
                id_horario_excluir=id_horario,
            )

        # 3. Convertir a objetos time para BD
        hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
        hf = datetime.strptime(dto.hora_fin, "%H:%M").time()

        # 4. Persistir
        self._repo.actualizar(
            id_horario=id_horario,
            id_asignacion=dto.id_asignacion,
            id_docente=dto.id_docente,
            id_aula=dto.id_aula,
            id_periodo=dto.id_periodo,
            dia=dto.dia,
            hora_inicio=hi,
            hora_fin=hf,
            total_horas=dto.total_horas,
            id_semestre=dto.id_semestre,
        )
        self._repo.commit()
