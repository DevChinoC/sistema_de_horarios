"""
Reglas de negocio para validación de docentes.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from domain.exceptions.horario_exceptions import HorarioInvalidoException


class DocenteValidator:
    """Valida las reglas de negocio relacionadas con docentes."""

    MIN_LONGITUD_NOMBRE = 2
    MAX_LONGITUD_NOMBRE = 200

    def validar_nombre(self, nombre: str) -> None:
        """Valida que el nombre del docente sea correcto.

        Args:
            nombre: Nombre del docente a validar.

        Raises:
            HorarioInvalidoException: Si el nombre no cumple las reglas.
        """
        if not isinstance(nombre, str):
            raise HorarioInvalidoException(
                campo="nombre",
                razon="El nombre debe ser una cadena de texto.",
            )
        nombre = nombre.strip()
        if not nombre:
            raise HorarioInvalidoException(
                campo="nombre",
                razon="El nombre del docente no puede estar vacío.",
            )
        if len(nombre) < self.MIN_LONGITUD_NOMBRE:
            raise HorarioInvalidoException(
                campo="nombre",
                razon=f"El nombre debe tener al menos {self.MIN_LONGITUD_NOMBRE} caracteres.",
            )
        if len(nombre) > self.MAX_LONGITUD_NOMBRE:
            raise HorarioInvalidoException(
                campo="nombre",
                razon=f"El nombre no puede exceder {self.MAX_LONGITUD_NOMBRE} caracteres.",
            )
