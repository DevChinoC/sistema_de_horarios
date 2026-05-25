"""
Value Object: Salon (Aula)

Representa el nombre de un salón/aula.
Elimina strings vacíos y nombres inválidos.

PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations


class Salon:
    """Nombre de salón/aula con validación automática."""

    MAX_LONGITUD = 80

    def __init__(self, nombre: str) -> None:
        """
        Args:
            nombre: Nombre del salón. No puede ser vacío.

        Raises:
            ValueError: Si el nombre es inválido.
        """
        if not isinstance(nombre, str):
            raise ValueError(
                f"Salon debe ser una cadena, recibido: {type(nombre)}"
            )
        self._nombre = nombre.strip()
        self._validar()

    def _validar(self) -> None:
        if not self._nombre:
            raise ValueError("El nombre del salón no puede estar vacío.")
        if len(self._nombre) > self.MAX_LONGITUD:
            raise ValueError(
                f"El nombre del salón excede {self.MAX_LONGITUD} caracteres."
            )

    @property
    def nombre(self) -> str:
        return self._nombre

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Salon):
            return self._nombre.lower() == other._nombre.lower()
        return False

    def __hash__(self) -> int:
        return hash(self._nombre.lower())

    def __repr__(self) -> str:
        return f"Salon('{self._nombre}')"

    def __str__(self) -> str:
        return self._nombre
