from sqlalchemy.orm import Session
from infrastructure.db.models import NivelAcademicoModel, PlanEstudiosModel


class PlanesRepository:
    """Consultas de solo-lectura para la vista 'Planes de estudios'."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_niveles(self) -> list[NivelAcademicoModel]:
        return (
            self._session.query(NivelAcademicoModel)
            .filter_by(activo=1)
            .order_by(NivelAcademicoModel.nombre)
            .all()
        )

    def obtener_planes_por_nivel(self, id_nivel: int) -> list[PlanEstudiosModel]:
        return (
            self._session.query(PlanEstudiosModel)
            .filter_by(activo=1, id_nivel=id_nivel)
            .order_by(PlanEstudiosModel.nombre)
            .all()
        )
