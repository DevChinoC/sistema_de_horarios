from sqlalchemy.orm import Session
from infrastructure.db.models import (
    PlanEstudiosModel, NivelAcademicoModel, LiesModel,
    SemestreModel, DetalleSemestreModel, TipoMateriaModel,
    MateriaTroncoModel, OptativaModel, AsignacionMateriaModel,
)


class PlanEstudiosRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def obtener_niveles(self)      -> list: return self._session.query(NivelAcademicoModel).filter_by(activo=1).all()
    def obtener_lies(self)         -> list: return self._session.query(LiesModel).filter_by(activo=1).all()
    def obtener_tipos_materia(self)-> list: return self._session.query(TipoMateriaModel).all()
    def obtener_materias_tronco(self)->list:return self._session.query(MateriaTroncoModel).all()
    def obtener_planes(self)       -> list: return self._session.query(PlanEstudiosModel).filter_by(activo=1).all()

    def crear_plan(self, nombre: str, id_nivel: int, lies_ids: list[int],
                   ruta_membrete: str | None = None) -> PlanEstudiosModel:
        plan = PlanEstudiosModel(nombre=nombre, id_nivel=id_nivel,
                                ruta_membrete=ruta_membrete)
        lies = self._session.query(LiesModel).filter(LiesModel.id_lies.in_(lies_ids)).all()
        plan.lies = lies
        self._session.add(plan)
        self._session.flush()
        return plan

    def crear_semestre(self, numero: int, id_plan: int) -> SemestreModel:
        s = SemestreModel(numero=numero, id_plan=id_plan)
        self._session.add(s); self._session.flush(); return s

    def crear_detalle(self, nombre_posicion: str, id_semestre: int, id_tipo: int, id_lies: int) -> DetalleSemestreModel:
        d = DetalleSemestreModel(nombre_posicion=nombre_posicion, id_semestre=id_semestre, id_tipo=id_tipo, id_lies=id_lies)
        self._session.add(d); self._session.flush(); return d

    def crear_asignacion_tronco(self, id_detalle: int, id_materia: int) -> AsignacionMateriaModel:
        a = AsignacionMateriaModel(id_detalle=id_detalle, id_materia=id_materia, id_optativa=None)
        self._session.add(a); self._session.flush(); return a

    def crear_asignacion_optativa(self, id_detalle: int, id_optativa: int) -> AsignacionMateriaModel:
        a = AsignacionMateriaModel(id_detalle=id_detalle, id_materia=None, id_optativa=id_optativa)
        self._session.add(a); self._session.flush(); return a

    def crear_nivel(self, nombre: str) -> NivelAcademicoModel:
        n = NivelAcademicoModel(nombre=nombre, activo=1)
        self._session.add(n); self._session.flush(); return n

    def commit(self)   -> None: self._session.commit()
    def rollback(self) -> None: self._session.rollback()