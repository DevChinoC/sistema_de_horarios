"""
Specification: SalonDisponibleSpecification.

Encapsula la regla de negocio:
  "Un salón está disponible si ningún horario existente ocupa
   ese salón en el mismo día y rango de horas."

PROHIBIDO: importar Flet, acceder a BD.
"""
from __future__ import annotations

from domain.entities.horario import Horario


class SalonDisponibleSpecification:
    """Verifica si un salón está libre en un rango dado.

    Uso:
        spec = SalonDisponibleSpecification(existentes)
        if spec.is_satisfied_by(nuevo_horario):
            print("Salón disponible")
    """

    def __init__(self, existentes: list[Horario]) -> None:
        self._existentes = existentes

    def is_satisfied_by(self, horario: Horario) -> bool:
        """Retorna True si el salón del horario está disponible."""
        if horario.id_aula is None:
            return True  # sin aula asignada, no hay conflicto

        for ex in self._existentes:
            if ex.id_aula != horario.id_aula:
                continue
            if ex.id_horario == horario.id_horario:
                continue  # excluir el mismo horario (edición)
            if ex.traslapa(horario):
                return False
        return True

    def conflictos(self, horario: Horario) -> list[Horario]:
        """Retorna la lista de horarios que colisionan con el salón."""
        if horario.id_aula is None:
            return []
        return [
            ex for ex in self._existentes
            if ex.id_aula == horario.id_aula
            and ex.id_horario != horario.id_horario
            and ex.traslapa(horario)
        ]
