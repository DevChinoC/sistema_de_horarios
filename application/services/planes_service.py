from application.dto.planes_dto import NivelDTO, PlanDTO
from infrastructure.db.connection import DatabaseConnection
from infrastructure.repositories.planes_repository import PlanesRepository


class PlanesService:
    """Caso de uso: obtener niveles y planes desde la BD para la vista principal."""

    def __init__(self) -> None:
        self._db = DatabaseConnection()

    def obtener_niveles(self) -> list[NivelDTO]:
        session = self._db.get_session()
        try:
            return [
                NivelDTO(id=n.id_nivel, nombre=n.nombre)
                for n in PlanesRepository(session).obtener_niveles()
            ]
        finally:
            session.close()

    def obtener_planes_por_nivel(self, id_nivel: int) -> list[PlanDTO]:
        session = self._db.get_session()
        try:
            return [
                PlanDTO(id=p.id_plan, nombre=p.nombre, id_nivel=p.id_nivel)
                for p in PlanesRepository(session).obtener_planes_por_nivel(id_nivel)
            ]
        finally:
            session.close()
