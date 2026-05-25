"""
Reglas de negocio para validación de salones/aulas.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from domain.exceptions.horario_exceptions import HorarioInvalidoException


class SalonValidator:
    """Valida las reglas de negocio relacionadas con salones/aulas."""

    MIN_LONGITUD_NOMBRE = 1
    MAX_LONGITUD_NOMBRE = 100

    def validar_nombre(self, nombre: str) -> None:
        """Valida que el nombre del salón sea correcto.

        Args:
            nombre: Nombre del salón/aula a validar.

        Raises:
            HorarioInvalidoException: Si el nombre no cumple las reglas.
        """
        if not isinstance(nombre, str):
            raise HorarioInvalidoException(
                campo="nombre",
                razon="El nombre del salón debe ser una cadena de texto.",
            )
        nombre = nombre.strip()
        if not nombre:
            raise HorarioInvalidoException(
                campo="nombre",
                razon="El nombre del salón no puede estar vacío.",
            )
        if len(nombre) > self.MAX_LONGITUD_NOMBRE:
            raise HorarioInvalidoException(
                campo="nombre",
                razon=f"El nombre del salón no puede exceder {self.MAX_LONGITUD_NOMBRE} caracteres.",
            )
