"""
Value Object: Grupo

Representa el identificador de un grupo académico.
Elimina ints ambiguos que podrían confundirse con IDs de otras entidades.

PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations


class Grupo:
    """Identificador de grupo académico con validación.

    Ejemplos:
        >>> Grupo("A")
        >>> Grupo("01")
        >>> Grupo("")   # lanza ValueError
    """

    MAX_LONGITUD = 20

    def __init__(self, identificador: str) -> None:
        """
        Args:
            identificador: Etiqueta del grupo (ej: "A", "01", "Matutino").

        Raises:
            ValueError: Si el identificador es inválido.
        """
        if not isinstance(identificador, str):
            raise ValueError(
                f"Grupo debe ser una cadena, recibido: {type(identificador)}"
            )
        self._id = identificador.strip()
        self._validar()

    def _validar(self) -> None:
        if not self._id:
            raise ValueError("El identificador de grupo no puede estar vacío.")
        if len(self._id) > self.MAX_LONGITUD:
            raise ValueError(
                f"El identificador de grupo excede {self.MAX_LONGITUD} caracteres."
            )

    @property
    def identificador(self) -> str:
        return self._id

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Grupo):
            return self._id == other._id
        return False

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"Grupo('{self._id}')"

    def __str__(self) -> str:
        return self._id
