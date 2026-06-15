"""Excepciones de dominio del sistema de horarios."""
from domain.exceptions.horario_exceptions import (
    HorarioConflictException,
    HorarioInvalidoException,
    PeriodoInvalidoException,
)

__all__ = [
    "HorarioConflictException",
    "HorarioInvalidoException",
    "PeriodoInvalidoException",
]

