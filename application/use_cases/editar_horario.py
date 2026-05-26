"""
Caso de uso: Editar Horario

Responsabilidad única: orquestar la actualización de un horario existente.
- Consulta conflictos desde la BD real (excluyendo el horario editado).
- Valida reglas de negocio vía HorarioValidator.
- Persiste mediante IHorarioRepository.

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
        2. Consultar conflictos desde BD real (excluye el propio horario).
        3. Validar con HorarioValidator.
        4. Persistir los cambios mediante el repositorio.

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
    ) -> None:
        """Actualiza un horario existente.

        Args:
            id_horario: ID del horario a actualizar.
            dto: Nuevos datos del horario.

        Raises:
            HorarioInvalidoException: Datos inválidos.
            HorarioConflictException: Conflicto de horario.
        """
        # 1. Construir entidad actualizada (valida hora_inicio < hora_fin)
        id_materia = self._repo.obtener_id_materia_de_asignacion(dto.id_asignacion)
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
            id_materia=id_materia,
            id_horario=id_horario,
            total_horas=dto.total_horas,
        )

        # 2. Consultar conflictos desde BD real (excluir el propio horario)
        existentes = self._repo.obtener_horarios_conflictivos(
            id_plan=dto.id_plan,
            id_semestre=dto.id_semestre,
            dia=dto.dia,
            id_lies=dto.id_lies,
            id_horario_excluir=id_horario,
        )

        # 3. Validar conflictos
        self._validator.validar_traslapes(
            actualizado,
            existentes,
            id_horario_excluir=id_horario,
        )

        # 4. Convertir a objetos time para BD
        hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
        hf = datetime.strptime(dto.hora_fin, "%H:%M").time()

        # 5. Persistir
        self._repo.actualizar_horario(
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

    def ejecutar_detalle(
        self,
        id_detalle: int,
        dto: GuardarHorarioDTO,
    ) -> None:
        """Actualiza UN detalle específico (por id_detalle_horario).

        Flujo:
            1. Obtener el detalle para conocer su id_horario padre.
            2. Construir entidad Horario para validación.
            3. Consultar conflictos (excluir el horario padre).
            4. Validar.
            5. Persistir: UPDATE detalle + UPDATE horario maestro.

        Args:
            id_detalle: ID del detalle a actualizar (PK de detalle_horario).
            dto: Nuevos datos del horario.
        """
        # 1. Obtener detalle actual para conocer id_horario padre
        detalle_raw = self._repo.obtener_detalle_por_id(id_detalle)
        if detalle_raw is None:
            raise HorarioInvalidoException("Detalle de horario no encontrado.")
        id_horario = detalle_raw.id_horario

        # 2. Construir entidad actualizada (valida hora_inicio < hora_fin)
        id_materia = self._repo.obtener_id_materia_de_asignacion(dto.id_asignacion)
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
            id_materia=id_materia,
            id_horario=id_horario,
            total_horas=dto.total_horas,
        )

        # 3. Consultar conflictos desde BD real (excluir el horario padre)
        existentes = self._repo.obtener_horarios_conflictivos(
            id_plan=dto.id_plan,
            id_semestre=dto.id_semestre,
            dia=dto.dia,
            id_lies=dto.id_lies,
            id_horario_excluir=id_horario,
        )

        # 4. Validar conflictos
        self._validator.validar_traslapes(
            actualizado,
            existentes,
            id_horario_excluir=id_horario,
        )

        # 5. Convertir a objetos time para BD
        hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
        hf = datetime.strptime(dto.hora_fin, "%H:%M").time()

        # 6. Persistir: UPDATE detalle in-place (SIN delete/recreate)
        self._repo.actualizar_detalle_horario(
            id_detalle=id_detalle,
            id_asignacion=dto.id_asignacion,
            id_semestre=dto.id_semestre,
            dia=dto.dia,
            hora_inicio=hi,
            hora_fin=hf,
            total_horas=dto.total_horas,
        )

        # 7. Actualizar HorarioModel padre (docente, aula, periodo)
        self._repo.actualizar_horario_maestro(
            id_horario=id_horario,
            id_docente=dto.id_docente,
            id_aula=dto.id_aula,
            id_periodo=dto.id_periodo,
            total_horas=dto.total_horas,
        )
        self._repo.commit()
