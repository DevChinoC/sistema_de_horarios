"""
Contrato abstracto del repositorio de planes.
Todas las implementaciones concretas deben heredar de IPlanRepository.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.dto.plan_estudios_dto import FilaMateriaDTO


class IPlanRepository(ABC):
    """Interfaz que define las operaciones de persistencia para planes de estudio."""

    # ── Catálogos: nivel académico ───────────────────────────────────────────

    @abstractmethod
    def obtener_niveles(self) -> list:
        """Retorna lista de tuplas (id_nivel, nombre) para niveles activos."""
        ...

    @abstractmethod
    def crear_nivel(self, nombre: str) -> int:
        """Inserta un nuevo nivel académico y retorna su id."""
        ...

    # ── Tipo de materia ─────────────────────────────────────────────────────

    @abstractmethod
    def obtener_id_tipo(self, nombre: str) -> int:
        """Retorna el id_tipo para un nombre de tipo de materia."""
        ...

    # ── LIES ────────────────────────────────────────────────────────────────

    @abstractmethod
    def obtener_todas_lies(self) -> list[int]:
        """Retorna todos los id_lies activos."""
        ...

    # ── Plan de estudios ────────────────────────────────────────────────────

    @abstractmethod
    def crear_plan(self, nombre: str, id_nivel: int, fecha_inicio: str | None = None):
        """Crea un nuevo plan de estudios y retorna la entidad creada."""
        ...

    @abstractmethod
    def vincular_plan_lies(self, id_plan: int, ids_lies: list[int]) -> None:
        """Vincula un plan con todas las LIES (relación N:M)."""
        ...

    # ── Semestres ───────────────────────────────────────────────────────────

    @abstractmethod
    def crear_semestres_base(self, id_plan: int) -> None:
        """Inserta los semestres 0-8 para el plan dado."""
        ...

    @abstractmethod
    def obtener_semestre(self, numero: int, id_plan: int) -> int:
        """Retorna el id_semestre para un número y plan dados."""
        ...

    # ── Detalle semestre ────────────────────────────────────────────────────

    @abstractmethod
    def crear_detalle(self, id_semestre: int, id_tipo: int, id_lies: int) -> int:
        """Inserta un registro en detalle_semestre y retorna su id."""
        ...

    # ── Materias ─────────────────────────────────────────────────────────────

    @abstractmethod
    def guardar_materia(
        self, nombre: str, tipo: str, id_detalle: int, id_plan: int
    ) -> None:
        """Persiste una materia (tronco u optativa) y la asigna al detalle."""
        ...
