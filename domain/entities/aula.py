"""
Entidad de dominio: Aula

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from domain.exceptions.horario_exceptions import HorarioInvalidoException


class Aula:
    """Aula o salón donde se imparte una materia."""

    MAX_NOMBRE = 100

    def __init__(self, id_aula: int, nombre: str) -> None:
        """
        Args:
            id_aula: Identificador único en BD.
            nombre: Nombre o clave del aula (ej: "A-101", "Lab Cómputo").

        Raises:
            HorarioInvalidoException: Si el nombre es inválido.
        """
        self.id_aula = id_aula
        self.nombre = nombre.strip() if isinstance(nombre, str) else str(nombre)
        self.validar()

    def validar(self) -> None:
        """Valida los datos del aula.

        Raises:
            HorarioInvalidoException: Si el nombre está vacío o es muy largo.
        """
        if not self.nombre:
            raise HorarioInvalidoException(
                campo="nombre",
                razon="El nombre del aula no puede estar vacío.",
            )
        if len(self.nombre) > self.MAX_NOMBRE:
            raise HorarioInvalidoException(
                campo="nombre",
                razon=f"El nombre del aula excede {self.MAX_NOMBRE} caracteres.",
            )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Aula):
            return self.id_aula == other.id_aula
        return False

    def __hash__(self) -> int:
        return hash(self.id_aula)

    def __repr__(self) -> str:
        return f"Aula(id={self.id_aula}, nombre='{self.nombre}')"

    def __str__(self) -> str:
        return self.nombre
