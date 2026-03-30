from sqlalchemy import Column, Integer, String, ForeignKey, Table
from infrastructure.db.connection import Base

plan_lies = Table(
    "plan_lies",
    Base.metadata,
    Column("id_plan", ForeignKey("plan_estudios.id_plan"), primary_key=True),
    Column("id_lies", ForeignKey("lies_horarios.id_lies"), primary_key=True),
)

class NivelAcademico(Base):
    __tablename__ = "nivel_academico"

    id_nivel = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)


class PlanEstudios(Base):
    __tablename__ = "plan_estudios"

    id_plan = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    activo = Column(Integer, default=1)
    id_nivel = Column(Integer, ForeignKey("nivel_academico.id_nivel"), nullable=False)