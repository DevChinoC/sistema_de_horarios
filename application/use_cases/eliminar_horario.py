"""
Caso de uso: Eliminar Horario

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a BD directamente aquí.
"""
from __future__ import annotations

from application.interfaces.horario_repository_interface import IHorarioRepository


class EliminarHorarioUseCase:
    """Orquesta la eliminación de un horario existente.

    Flujo:
        1. Verificar que el horario exista.
        2. Eliminar del repositorio.
        3. Confirmar la transacción.

    Raises:
        ValueError: Si el horario no existe en BD.
    """

    def __init__(self, repo: IHorarioRepository) -> None:
        self._repo = repo

    def ejecutar(self, id_horario: int) -> None:
        """Elimina el horario con el ID dado.

        Args:
            id_horario: ID del horario a eliminar.

        Raises:
            ValueError: Si no existe el horario.
        """
        detalle = self._repo.obtener_por_id(id_horario)
        if detalle is None:
            raise ValueError(
                f"No se encontró el horario con ID {id_horario}."
            )
        self._repo.eliminar(id_horario)
        self._repo.commit()
