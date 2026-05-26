"""
Interfaz abstracta del repositorio de horarios.

Define el contrato que deben cumplir todas las implementaciones
concretas (MySQL, SQLite, in-memory para tests, etc.).

PROHIBIDO: importar Flet aquí.
PROHIBIDO: implementar lógica de negocio aquí.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.horario import Horario
    from application.dto.horario_dto import (
        HorarioRegistradoDTO,
        HorarioDetalleDTO,
        LiesDTO,
        SemestreDTO,
        UnidadAprendizajeDTO,
        DocenteDTO,
        AulaDTO,
        PeriodoDTO,
    )


class IHorarioRepository(ABC):
    """Contrato abstracto del repositorio de horarios.

    Todas las implementaciones concretas deben heredar de esta clase.
    El flujo correcto es:
        View → Controller → UseCase → Service → Repository → MySQL
    """

    # ── Horarios ──────────────────────────────────────────────

    @abstractmethod
    def crear(
        self,
        id_plan_generado: int,
        id_asignacion: int,
        id_docente: int,
        id_aula: int,
        dia: str,
        hora_inicio,
        hora_fin,
        total_horas: float,
        id_semestre: int | None,
    ) -> int:
        """Persiste un nuevo horario y retorna su id_horario."""
        ...

    @abstractmethod
    def actualizar(
        self,
        id_horario: int,
        id_asignacion: int,
        id_docente: int,
        id_aula: int,
        id_periodo: int,
        dia: str,
        hora_inicio,
        hora_fin,
        total_horas: float,
        id_semestre: int | None,
    ) -> None:
        """Actualiza un horario existente."""
        ...

    @abstractmethod
    def eliminar(self, id_horario: int) -> None:
        """Elimina un horario por ID."""
        ...

    @abstractmethod
    def obtener_detalle_por_id(self, id_detalle: int) -> "HorarioDetalleDTO | None":
        """Retorna el detalle de un horario por id_detalle_horario."""
        ...

    @abstractmethod
    def actualizar_detalle_horario(
        self,
        id_detalle: int,
        id_asignacion: int,
        id_semestre: int | None,
        dia: str,
        hora_inicio,
        hora_fin,
        total_horas: int,
    ) -> None:
        """Actualiza UN detalle in-place — SIN delete/recreate."""
        ...

    @abstractmethod
    def actualizar_horario_maestro(
        self,
        id_horario: int,
        id_docente: int,
        id_aula: int,
        id_periodo: int,
        total_horas: int,
    ) -> None:
        """Actualiza los campos del HorarioModel padre (docente, aula, periodo)."""
        ...

    @abstractmethod
    def obtener_id_materia_de_asignacion(self, id_asignacion: int) -> int | None:
        """Retorna el id_materia de tronco o None si es optativa."""
        ...

    @abstractmethod
    def obtener_por_id(self, id_horario: int) -> "HorarioDetalleDTO | None":
        """Retorna el detalle de un horario o None si no existe."""
        ...

    @abstractmethod
    def obtener_filtrados(
        self,
        id_plan: int,
        id_lies: int,
        id_semestre: int,
        id_semestre_opt: int | None = None,
    ) -> list["HorarioRegistradoDTO"]:
        """Retorna horarios filtrados por plan, LIES y semestre."""
        ...

    @abstractmethod
    def obtener_de_plan_generado(
        self, id_plan_generado: int,
    ) -> list["HorarioRegistradoDTO"]:
        """Retorna todos los horarios de un plan_generado."""
        ...

    # ── Plan generado ─────────────────────────────────────────

    @abstractmethod
    def obtener_o_crear_plan_generado(
        self,
        id_plan: int,
        id_periodo: int,
        id_lies: int,
    ) -> object:
        """Obtiene o crea el plan_generado para el plan/periodo/LIES dados."""
        ...

    @abstractmethod
    def eliminar_plan_generado(self, id_plan_generado: int) -> None:
        """Elimina un plan generado y todos sus horarios."""
        ...

    # ── Catálogos ─────────────────────────────────────────────

    @abstractmethod
    def obtener_docentes(self) -> list["DocenteDTO"]:
        """Retorna todos los docentes."""
        ...

    @abstractmethod
    def crear_docente(self, nombre: str) -> "DocenteDTO":
        """Crea un nuevo docente y lo retorna."""
        ...

    @abstractmethod
    def obtener_aulas(self) -> list["AulaDTO"]:
        """Retorna todas las aulas."""
        ...

    @abstractmethod
    def crear_aula(self, nombre: str) -> "AulaDTO":
        """Crea una nueva aula y la retorna."""
        ...

    @abstractmethod
    def crear_periodo(self, nombre: str) -> "PeriodoDTO":
        """Crea o recupera un periodo y lo retorna."""
        ...

    # ── Unidades y semestres ──────────────────────────────────

    @abstractmethod
    def obtener_semestres(self, id_plan: int) -> list["SemestreDTO"]:
        """Retorna los semestres del plan."""
        ...

    @abstractmethod
    def obtener_unidades(
        self,
        id_plan: int,
        id_lies: int,
        id_semestre: int | None,
    ) -> list["UnidadAprendizajeDTO"]:
        """Retorna las unidades de aprendizaje del plan/lies/semestre."""
        ...

    @abstractmethod
    def obtener_id_materia(self, id_asignacion: int) -> int | None:
        """Retorna el id_materia de tronco o None si es optativa."""
        ...

    # ── Validación de conflictos ─────────────────────────────

    @abstractmethod
    def obtener_horarios_conflictivos(
        self,
        id_plan: int,
        id_semestre: int | None,
        dia: str,
        id_lies: int | None = None,
        id_horario_excluir: int | None = None,
    ) -> list["Horario"]:
        """Retorna horarios candidatos a conflicto para validación.

        Solo trae candidatos del mismo plan/semestre/día.
        Retorna entidades Horario del dominio.
        """
        ...

    # ── Transacciones ─────────────────────────────────────────

    @abstractmethod
    def commit(self) -> None:
        """Confirma la transacción actual."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Deshace la transacción actual."""
        ...
