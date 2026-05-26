"""
Caso de uso: Crear Horario

Responsabilidad única: orquestar la creación de un nuevo bloque horario.
- Construye la entidad Horario (con sus value objects).
- Consulta conflictos desde la BD real (no desde cachés).
- Valida reglas de negocio vía HorarioValidator.
- Persiste mediante IHorarioRepository.
- Lanza excepciones de dominio (nunca retorna tuplas bool/str).

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a BD directamente aquí.
"""
from __future__ import annotations

from datetime import datetime

from application.dto.horario_dto import GuardarHorarioDTO
from application.interfaces.horario_repository_interface import IHorarioRepository
from domain.entities.horario import Horario
from domain.exceptions.horario_exceptions import (
    HorarioInvalidoException,
    PeriodoInvalidoException,
)
from domain.rules.horario_validator import HorarioValidator


class CrearHorarioUseCase:
    """Orquesta la creación de un nuevo horario.

    Flujo:
        1. Crear la entidad Horario (valida sus invariantes).
        2. Consultar conflictos desde BD real.
        3. Validar con HorarioValidator.
        4. Obtener o crear el plan_generado.
        5. Persistir mediante el repositorio.
        6. Retornar el id_horario creado.

    Raises:
        HorarioInvalidoException: Si los datos del horario son inválidos.
        HorarioConflictException: Si hay conflicto con horarios existentes.
        PeriodoInvalidoException: Si el periodo no puede crearse.
    """

    def __init__(
        self,
        repo: IHorarioRepository,
        validator: HorarioValidator,
    ) -> None:
        self._repo = repo
        self._validator = validator

    def ejecutar(self, dto: GuardarHorarioDTO) -> int:
        """Crea un nuevo horario y retorna su id_horario.

        Args:
            dto: Datos del horario a crear.

        Returns:
            El id_horario del registro creado en BD.

        Raises:
            HorarioInvalidoException: Datos inválidos.
            HorarioConflictException: Conflicto de horario.
        """
        # 1. Construir la entidad (valida invariantes: hora_inicio < hora_fin)
        id_materia = self._repo.obtener_id_materia_de_asignacion(dto.id_asignacion)
        nuevo = Horario(
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
            total_horas=dto.total_horas,
        )

        # 2. Consultar conflictos desde BD real (no desde cachés)
        existentes = self._repo.obtener_horarios_conflictivos(
            id_plan=dto.id_plan,
            id_semestre=dto.id_semestre,
            dia=dto.dia,
            id_lies=dto.id_lies,
        )

        # 3. Validar con HorarioValidator
        self._validator.validar_traslapes(nuevo, existentes)

        # 4. Obtener o crear el plan_generado en BD
        pg = self._repo.obtener_o_crear_plan_generado(
            dto.id_plan, dto.id_periodo, dto.id_lies
        )

        # 5. Convertir hora_inicio y hora_fin a objetos time para BD
        hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
        hf = datetime.strptime(dto.hora_fin, "%H:%M").time()

        # 6. Persistir
        h = self._repo.crear_horario(
            id_plan_generado=pg.id_plan_generado,
            id_asignacion=dto.id_asignacion,
            id_docente=dto.id_docente,
            id_aula=dto.id_aula,
            dia=dto.dia,
            hora_inicio=hi,
            hora_fin=hf,
            total_horas=dto.total_horas,
            id_semestre=dto.id_semestre,
        )
        self._repo.commit()
        return h.id_horario
