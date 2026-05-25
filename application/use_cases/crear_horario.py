"""
Caso de uso: Crear Horario

Responsabilidad única: orquestar la creación de un nuevo bloque horario.
- Construye la entidad Horario (con sus value objects).
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
        2. Obtener o crear el plan_generado.
        3. Obtener el id_materia (tronco o None).
        4. Construir lista de horarios existentes para validar conflictos.
        5. Validar con HorarioValidator.
        6. Persistir mediante el repositorio.
        7. Retornar el id_horario creado.

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

    def ejecutar(
        self,
        dto: GuardarHorarioDTO,
        horarios_existentes: list[Horario] | None = None,
    ) -> int:
        """Crea un nuevo horario y retorna su id_horario.

        Args:
            dto: Datos del horario a crear.
            horarios_existentes: Lista de objetos Horario ya registrados
                en la sesión (para validar conflictos en memoria).
                Si es None, no se validan conflictos de sesión.

        Returns:
            El id_horario del registro creado en BD.

        Raises:
            HorarioInvalidoException: Datos inválidos.
            HorarioConflictException: Conflicto de horario.
        """
        # 1. Construir la entidad (valida invariantes: hora_inicio < hora_fin)
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
            id_materia=self._repo.obtener_id_materia(dto.id_asignacion),
            total_horas=dto.total_horas,
        )

        # 2. Validar conflictos contra horarios existentes en sesión
        if horarios_existentes:
            self._validator.validar_traslapes(nuevo, horarios_existentes)

        # 3. Obtener o crear el plan_generado en BD
        pg = self._repo.obtener_o_crear_plan_generado(
            dto.id_plan, dto.id_periodo, dto.id_lies
        )

        # 4. Convertir hora_inicio y hora_fin a objetos time para BD
        hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
        hf = datetime.strptime(dto.hora_fin, "%H:%M").time()

        # 5. Persistir
        id_horario = self._repo.crear(
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
        return id_horario
