"""
Caso de uso: Guardar Plan

Orquesta la persistencia de múltiples horarios como un plan completo.
Útil para guardar en lote cuando el usuario finaliza el llenado de un semestre.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a BD directamente aquí.
"""
from __future__ import annotations

from application.dto.horario_dto import GuardarHorarioDTO
from application.interfaces.horario_repository_interface import IHorarioRepository
from application.use_cases.crear_horario import CrearHorarioUseCase
from domain.entities.horario import Horario
from domain.exceptions.horario_exceptions import HorarioConflictException
from domain.rules.horario_validator import HorarioValidator


class GuardarPlanUseCase:
    """Orquesta la creación de múltiples horarios como una unidad.

    Flujo:
        1. Iterar sobre cada DTO de horario.
        2. Crear cada horario usando CrearHorarioUseCase.
        3. Agregar el horario creado a la lista de existentes para que
           los siguientes en el lote sean validados contra él.
        4. Si alguno falla, no continúa (fail-fast).

    Raises:
        HorarioInvalidoException: Si algún horario tiene datos inválidos.
        HorarioConflictException: Si algún horario en el lote genera conflicto.
    """

    def __init__(
        self,
        repo: IHorarioRepository,
        validator: HorarioValidator,
    ) -> None:
        self._repo = repo
        self._validator = validator
        self._crear_uc = CrearHorarioUseCase(repo, validator)

    def ejecutar(
        self,
        dtos: list[GuardarHorarioDTO],
        horarios_existentes: list[Horario] | None = None,
    ) -> list[int]:
        """Guarda un lote de horarios.

        Args:
            dtos: Lista de DTOs a persistir. Todos deben pertenecer
                  al mismo plan/periodo/lies.
            horarios_existentes: Horarios ya en sesión para validación.

        Returns:
            Lista de ids_horario de los registros creados, en el mismo
            orden que los dtos de entrada.

        Raises:
            HorarioInvalidoException: Datos inválidos en algún DTO.
            HorarioConflictException: Conflicto en algún horario del lote.
        """
        acumulados: list[Horario] = list(horarios_existentes or [])
        ids_creados: list[int] = []

        for dto in dtos:
            id_nuevo = self._crear_uc.ejecutar(dto, acumulados)
            ids_creados.append(id_nuevo)
            # Agregar el recién creado a la lista de existentes
            # para validar los siguientes del mismo lote
            acumulados.append(Horario(
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
                id_horario=id_nuevo,
                total_horas=dto.total_horas,
            ))

        return ids_creados
