from sqlalchemy import (
    Column, Integer, SmallInteger, String, ForeignKey,
    Enum, Time, Date, CheckConstraint, Table
)
from sqlalchemy.orm import relationship
from infrastructure.db.connection import Base


plan_lies_table = Table(
    "plan_lies", Base.metadata,
    Column("id_plan", Integer, ForeignKey("plan_estudios.id_plan"), primary_key=True),
    Column("id_lies", Integer, ForeignKey("lies_horarios.id_lies"),  primary_key=True),
)


class LiesModel(Base):
    __tablename__ = "lies_horarios"
    id_lies = Column(Integer, primary_key=True, autoincrement=True)
    nombre  = Column(String(100), nullable=False, unique=True)
    activo  = Column(SmallInteger, default=1)
    planes  = relationship("PlanEstudiosModel", secondary=plan_lies_table, back_populates="lies")
    detalles = relationship("DetalleSemestreModel", back_populates="lies")


class NivelAcademicoModel(Base):
    __tablename__ = "nivel_academico"
    id_nivel = Column(Integer, primary_key=True, autoincrement=True)
    nombre   = Column(String(100), nullable=False, unique=True)
    activo   = Column(SmallInteger, default=1)
    planes   = relationship("PlanEstudiosModel", back_populates="nivel")


class PlanEstudiosModel(Base):
    __tablename__ = "plan_estudios"
    id_plan        = Column(Integer, primary_key=True, autoincrement=True)
    nombre         = Column(String(150), nullable=False)
    activo         = Column(SmallInteger, default=1)
    id_nivel       = Column(Integer, ForeignKey("nivel_academico.id_nivel"), nullable=False)
    nivel    = relationship("NivelAcademicoModel", back_populates="planes")
    lies     = relationship("LiesModel", secondary=plan_lies_table, back_populates="planes")
    semestres       = relationship("SemestreModel",     back_populates="plan")
    optativas       = relationship("OptativaModel",     back_populates="plan")
    planes_generados = relationship("PlanGeneradoModel", back_populates="plan")


class SemestreModel(Base):
    __tablename__ = "semestres"
    id_semestre = Column(Integer, primary_key=True, autoincrement=True)
    numero      = Column(Integer, nullable=False)
    id_plan     = Column(Integer, ForeignKey("plan_estudios.id_plan"), nullable=False)
    plan     = relationship("PlanEstudiosModel",    back_populates="semestres")
    detalles = relationship("DetalleSemestreModel", back_populates="semestre")


class TipoMateriaModel(Base):
    __tablename__ = "tipo_materia"
    id_tipo  = Column(Integer, primary_key=True, autoincrement=True)
    nombre   = Column(String(100), nullable=False, unique=True)
    detalles = relationship("DetalleSemestreModel", back_populates="tipo")


class DetalleSemestreModel(Base):
    __tablename__ = "detalle_semestre"
    id_detalle      = Column(Integer, primary_key=True, autoincrement=True)
    nombre_posicion = Column(String(100))
    id_semestre     = Column(Integer, ForeignKey("semestres.id_semestre"),    nullable=False)
    id_tipo         = Column(Integer, ForeignKey("tipo_materia.id_tipo"),     nullable=False)
    id_lies         = Column(Integer, ForeignKey("lies_horarios.id_lies"),    nullable=False)
    semestre     = relationship("SemestreModel",        back_populates="detalles")
    tipo         = relationship("TipoMateriaModel",     back_populates="detalles")
    lies         = relationship("LiesModel",            back_populates="detalles")
    asignaciones = relationship("AsignacionMateriaModel", back_populates="detalle")


class MateriaTroncoModel(Base):
    __tablename__ = "materias_tronco"
    id_materia   = Column(Integer, primary_key=True, autoincrement=True)
    nombre       = Column(String(150), nullable=False, unique=True)
    asignaciones = relationship("AsignacionMateriaModel", back_populates="materia")


class OptativaModel(Base):
    __tablename__ = "optativas"
    id_optativa  = Column(Integer, primary_key=True, autoincrement=True)
    nombre       = Column(String(150), nullable=False)
    id_plan      = Column(Integer, ForeignKey("plan_estudios.id_plan"), nullable=False)
    plan         = relationship("PlanEstudiosModel",      back_populates="optativas")
    asignaciones = relationship("AsignacionMateriaModel", back_populates="optativa")


class AsignacionMateriaModel(Base):
    __tablename__ = "asignacion_materia"
    __table_args__ = (
        CheckConstraint(
            "(id_materia IS NOT NULL AND id_optativa IS NULL) OR "
            "(id_materia IS NULL  AND id_optativa IS NOT NULL)",
            name="chk_materia_optativa",
        ),
    )
    id_asignacion = Column(Integer, primary_key=True, autoincrement=True)
    id_detalle    = Column(Integer, ForeignKey("detalle_semestre.id_detalle"),    nullable=False)
    id_materia    = Column(Integer, ForeignKey("materias_tronco.id_materia"),     nullable=True)
    id_optativa   = Column(Integer, ForeignKey("optativas.id_optativa"),          nullable=True)
    detalle  = relationship("DetalleSemestreModel", back_populates="asignaciones")
    materia  = relationship("MateriaTroncoModel",   back_populates="asignaciones")
    optativa = relationship("OptativaModel",        back_populates="asignaciones")


class PeriodoEscolarModel(Base):
    __tablename__ = "periodo_escolar"
    id_periodo   = Column(Integer, primary_key=True, autoincrement=True)
    nombre       = Column(String(150), nullable=False)
    fecha_inicio = Column(Date)
    fecha_fin    = Column(Date)
    planes_generados = relationship("PlanGeneradoModel", back_populates="periodo")


class PlanGeneradoModel(Base):
    __tablename__ = "plan_generado"
    id_plan_generado = Column(Integer, primary_key=True, autoincrement=True)
    id_plan          = Column(Integer, ForeignKey("plan_estudios.id_plan"),      nullable=False)
    id_periodo       = Column(Integer, ForeignKey("periodo_escolar.id_periodo"), nullable=False)
    plan    = relationship("PlanEstudiosModel",  back_populates="planes_generados")
    periodo = relationship("PeriodoEscolarModel", back_populates="planes_generados")
    horarios = relationship("HorarioModel",      back_populates="plan_generado")


class DocenteModel(Base):
    __tablename__ = "docentes"
    id_docente = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String(150), nullable=False, unique=True)
    horarios   = relationship("HorarioModel", back_populates="docente")


class AulaModel(Base):
    __tablename__ = "aulas"
    id_aula  = Column(Integer, primary_key=True, autoincrement=True)
    nombre   = Column(String(100), nullable=False, unique=True)
    horarios = relationship("HorarioModel", back_populates="aula")


class HorarioModel(Base):
    __tablename__ = "horarios"
    id_horario       = Column(Integer, primary_key=True, autoincrement=True)
    id_plan_generado = Column(Integer, ForeignKey("plan_generado.id_plan_generado"),   nullable=False)
    id_docente       = Column(Integer, ForeignKey("docentes.id_docente"),              nullable=False)
    id_aula          = Column(Integer, ForeignKey("aulas.id_aula"),                    nullable=False)
    total_horas      = Column(Integer)
    plan_generado = relationship("PlanGeneradoModel", back_populates="horarios")
    docente       = relationship("DocenteModel",       back_populates="horarios")
    aula          = relationship("AulaModel",           back_populates="horarios")
    detalles      = relationship("DetalleHorarioModel", back_populates="horario",
                                 cascade="all, delete-orphan")


class DetalleHorarioModel(Base):
    __tablename__ = "detalle_horario"
    id_detalle_horario = Column(Integer, primary_key=True, autoincrement=True)
    id_horario         = Column(Integer, ForeignKey("horarios.id_horario"), nullable=False)
    id_asignacion      = Column(Integer, ForeignKey("asignacion_materia.id_asignacion"), nullable=False)
    dia          = Column(Enum("Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"), nullable=False)
    hora_inicio  = Column(Time,    nullable=False)
    hora_fin     = Column(Time,    nullable=False)
    total_horas  = Column(Integer)
    horario      = relationship("HorarioModel",           back_populates="detalles")
    asignacion   = relationship("AsignacionMateriaModel")