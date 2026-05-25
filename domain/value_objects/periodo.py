"""
Value Object: Periodo

Representa un periodo académico (ej: "Feb-Jun 2024").
Garantiza que el periodo no esté vacío.

PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations

import re


class Periodo:
    """Periodo académico inmutable con validación automática.

    Ejemplos:
        >>> Periodo("Feb-Jun 2024")
        >>> Periodo("Ago-Dic 2025")
        >>> Periodo("")    # lanza PeriodoInvalidoException
    """

    # Longitud máxima razonable para un nombre de periodo
    MAX_LONGITUD = 100

    def __init__(self, nombre: str) -> None:
        """
        Args:
            nombre: Nombre del periodo. No puede ser vacío ni solo espacios.

        Raises:
            ValueError: Si el nombre es inválido.
        """
        if not isinstance(nombre, str):
            raise ValueError(
                f"Periodo debe ser una cadena, recibido: {type(nombre)}"
            )
        self._nombre = nombre.strip()
        self._validar()

    def _validar(self) -> None:
        if not self._nombre:
            raise ValueError(
                "El periodo no puede estar vacío."
            )
        if len(self._nombre) > self.MAX_LONGITUD:
            raise ValueError(
                f"El periodo '{self._nombre[:30]}...' excede el máximo de "
                f"{self.MAX_LONGITUD} caracteres."
            )

    # ── API pública ───────────────────────────────────────────

    @property
    def nombre(self) -> str:
        return self._nombre

    # ── Comparaciones ─────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Periodo):
            return self._nombre == other._nombre
        if isinstance(other, str):
            return self._nombre == other.strip()
        return False

    def __hash__(self) -> int:
        return hash(self._nombre)

    def __repr__(self) -> str:
        return f"Periodo('{self._nombre}')"

    def __str__(self) -> str:
        return self._nombre
