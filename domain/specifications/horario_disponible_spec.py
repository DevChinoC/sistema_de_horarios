"""
Specifications de dominio para horarios.

Las Specifications encapsulan reglas de negocio complejas en objetos
reutilizables y componibles. Complementan a los validators que lanzan
excepciones; las specifications simplemente retornan bool + razón.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.entities.horario import Horario


class Specification(ABC):
    """Interfaz base para todas las specifications."""

    @abstractmethod
    def es_satisfecho_por(self, candidato: "Horario", contexto: dict) -> bool:
        """Evalúa si el candidato satisface la regla.

        Args:
            candidato: El horario a evaluar.
            contexto: Datos adicionales necesarios para la evaluación
                (ej: lista de horarios existentes, id_lies, etc.)

        Returns:
            True si la regla se satisface, False si no.
        """
        ...

    def razon_falla(self) -> str:
        """Describe por qué falló la última evaluación."""
        return self._razon_falla

    def __and__(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def __or__(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)

    def __invert__(self) -> "NotSpecification":
        return NotSpecification(self)


class AndSpecification(Specification):
    """Combina dos specifications con AND lógico."""

    def __init__(self, a: Specification, b: Specification) -> None:
        self._a = a
        self._b = b
        self._razon_falla = ""

    def es_satisfecho_por(self, candidato: "Horario", contexto: dict) -> bool:
        if not self._a.es_satisfecho_por(candidato, contexto):
            self._razon_falla = self._a.razon_falla()
            return False
        if not self._b.es_satisfecho_por(candidato, contexto):
            self._razon_falla = self._b.razon_falla()
            return False
        return True


class OrSpecification(Specification):
    """Combina dos specifications con OR lógico."""

    def __init__(self, a: Specification, b: Specification) -> None:
        self._a = a
        self._b = b
        self._razon_falla = ""

    def es_satisfecho_por(self, candidato: "Horario", contexto: dict) -> bool:
        if self._a.es_satisfecho_por(candidato, contexto):
            return True
        if self._b.es_satisfecho_por(candidato, contexto):
            return True
        self._razon_falla = (
            f"{self._a.razon_falla()} | {self._b.razon_falla()}"
        )
        return False


class NotSpecification(Specification):
    """Niega una specification."""

    def __init__(self, spec: Specification) -> None:
        self._spec = spec
        self._razon_falla = ""

    def es_satisfecho_por(self, candidato: "Horario", contexto: dict) -> bool:
        result = not self._spec.es_satisfecho_por(candidato, contexto)
        if not result:
            self._razon_falla = f"No se esperaba: {self._spec.razon_falla()}"
        return result


# ─────────────────────────────────────────────────────────────
# Specifications concretas
# ─────────────────────────────────────────────────────────────

class HorarioDisponibleSpecification(Specification):
    """Verifica si un horario puede asignarse sin conflictos.

    Contexto esperado:
        {
            "existentes": list[Horario],         # horarios ya registrados
            "id_horario_excluir": int | None,    # para edición
        }
    """

    def __init__(self) -> None:
        self._razon_falla = ""

    def es_satisfecho_por(self, candidato: "Horario", contexto: dict) -> bool:
        existentes: list["Horario"] = contexto.get("existentes", [])
        excluir: int | None = contexto.get("id_horario_excluir")

        candidatos = [
            h for h in existentes
            if h.id_horario != excluir
        ]

        for h_ex in candidatos:
            if candidato.traslapa(h_ex):
                self._razon_falla = (
                    f"El horario {candidato.dia} "
                    f"{candidato.hora_inicio}–{candidato.hora_fin} "
                    f"colisiona con otro bloque en "
                    f"{h_ex.dia} {h_ex.hora_inicio}–{h_ex.hora_fin}."
                )
                return False
        return True

    def razon_falla(self) -> str:
        return self._razon_falla


class TroncoConsistenteEntreLiesSpecification(Specification):
    """Verifica que el tronco común sea idéntico entre todas las LIES.

    Contexto esperado:
        {
            "horarios_cross_lies": list[Horario],  # misma materia, otras LIES
        }
    """

    def __init__(self) -> None:
        self._razon_falla = ""

    def es_satisfecho_por(self, candidato: "Horario", contexto: dict) -> bool:
        cross: list["Horario"] = contexto.get("horarios_cross_lies", [])
        if not cross:
            return True  # no hay restricción si no hay datos cross-LIES

        for h_ex in cross:
            if not candidato.mismo_rango_que(h_ex):
                self._razon_falla = (
                    "Esta materia de tronco común ya fue asignada en otra "
                    "LIES con diferente horario. Debe coincidir exactamente."
                )
                return False
            if candidato.id_aula != h_ex.id_aula:
                self._razon_falla = (
                    "Esta materia de tronco común ya fue asignada en otra "
                    "LIES con distinta aula."
                )
                return False
            if candidato.id_docente != h_ex.id_docente:
                self._razon_falla = (
                    "Esta materia de tronco común ya fue asignada en otra "
                    "LIES con distinto docente."
                )
                return False
        return True

    def razon_falla(self) -> str:
        return self._razon_falla
