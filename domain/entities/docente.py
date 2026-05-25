"""
Entidad de dominio: Docente

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from domain.exceptions.horario_exceptions import HorarioInvalidoException


class Docente:
    """Docente que imparte materias en el plan de estudios."""

    MAX_NOMBRE = 200

    def __init__(self, id_docente: int, nombre: str) -> None:
        """
        Args:
            id_docente: Identificador único en BD.
            nombre: Nombre completo del docente.

        Raises:
            HorarioInvalidoException: Si el nombre es inválido.
        """
        self.id_docente = id_docente
        self.nombre = nombre.strip() if isinstance(nombre, str) else str(nombre)
        self.validar()

    def validar(self) -> None:
        """Valida los datos del docente.

        Raises:
            HorarioInvalidoException: Si el nombre está vacío o es muy largo.
        """
        if not self.nombre:
            raise HorarioInvalidoException(
                campo="nombre",
                razon="El nombre del docente no puede estar vacío.",
            )
        if len(self.nombre) > self.MAX_NOMBRE:
            raise HorarioInvalidoException(
                campo="nombre",
                razon=f"El nombre excede {self.MAX_NOMBRE} caracteres.",
            )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Docente):
            return self.id_docente == other.id_docente
        return False

    def __hash__(self) -> int:
        return hash(self.id_docente)

    def __repr__(self) -> str:
        return f"Docente(id={self.id_docente}, nombre='{self.nombre}')"

    def __str__(self) -> str:
        return self.nombre
