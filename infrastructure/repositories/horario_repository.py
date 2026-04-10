from sqlalchemy.orm import Session
from sqlalchemy import func
from infrastructure.db.models import (
    PlanEstudiosModel, LiesModel, SemestreModel,
    DetalleSemestreModel, AsignacionMateriaModel,
    MateriaTroncoModel, OptativaModel,
    DocenteModel, AulaModel, PeriodoEscolarModel,
    HorarioModel, PlanGeneradoModel, TipoMateriaModel,
)


class HorarioRepository:
    """Acceso a datos para la vista de detalle de plan y registro de horarios."""

    def __init__(self, session: Session) -> None:
        self._s = session

    # ── Plan ─────────────────────────────────────────────────

    def obtener_plan(self, id_plan: int) -> PlanEstudiosModel | None:
        return self._s.query(PlanEstudiosModel).get(id_plan)

    # ── LIES del plan ─────────────────────────────────────────

    def obtener_lies_del_plan(self, id_plan: int) -> list[LiesModel]:
        plan = self._s.query(PlanEstudiosModel).get(id_plan)
        return list(plan.lies) if plan else []

    # ── Semestres del plan ────────────────────────────────────

    def obtener_semestres(self, id_plan: int) -> list[SemestreModel]:
        return (
            self._s.query(SemestreModel)
            .filter_by(id_plan=id_plan)
            .order_by(SemestreModel.numero)
            .all()
        )

    # ── Unidades de aprendizaje (materias tronco + optativas) ─
    # Filtra por lies y semestre; devuelve una lista de tuplas raw.

    def obtener_unidades(
        self,
        id_plan: int,
        id_lies: int,
        id_semestre: int | None = None,
    ) -> list[tuple]:
        """Retorna (id_detalle, id_asignacion, nombre, tipo, numero_semestre).

        Filtra siempre por lies. Opcionalmente filtra por semestre.
        """
        q = (
            self._s.query(
                DetalleSemestreModel.id_detalle,
                AsignacionMateriaModel.id_asignacion,
                DetalleSemestreModel.nombre_posicion,
                TipoMateriaModel.nombre.label("tipo"),
                SemestreModel.numero.label("numero_semestre"),
            )
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_detalle == DetalleSemestreModel.id_detalle)
            .join(SemestreModel,
                  SemestreModel.id_semestre == DetalleSemestreModel.id_semestre)
            .join(TipoMateriaModel,
                  TipoMateriaModel.id_tipo == DetalleSemestreModel.id_tipo)
            .filter(
                SemestreModel.id_plan == id_plan,
                DetalleSemestreModel.id_lies == id_lies,
            )
        )
        if id_semestre is not None:
            q = q.filter(DetalleSemestreModel.id_semestre == id_semestre)

        return q.order_by(SemestreModel.numero).all()

    # ── Catálogos ─────────────────────────────────────────────

    def obtener_docentes(self) -> list[DocenteModel]:
        return self._s.query(DocenteModel).order_by(DocenteModel.nombre).all()

    def obtener_aulas(self) -> list[AulaModel]:
        return self._s.query(AulaModel).order_by(AulaModel.nombre).all()

    def obtener_periodos(self) -> list[PeriodoEscolarModel]:
        return self._s.query(PeriodoEscolarModel).order_by(PeriodoEscolarModel.nombre).all()

    def obtener_tipos_materia(self) -> list[TipoMateriaModel]:
        return self._s.query(TipoMateriaModel).order_by(TipoMateriaModel.id_tipo).all()

    # ── Horarios registrados del plan ─────────────────────────

    def obtener_horarios_del_plan(self, id_plan: int) -> list[tuple]:
        """Retorna filas con todos los datos para la tabla inferior."""
        return (
            self._s.query(
                HorarioModel.id_horario,
                SemestreModel.numero.label("semestre"),
                DetalleSemestreModel.nombre_posicion.label("unidad"),
                DocenteModel.nombre.label("docente"),
                AulaModel.nombre.label("aula"),
                PeriodoEscolarModel.nombre.label("periodo"),
                HorarioModel.total_horas,
                HorarioModel.dia,
                HorarioModel.hora_inicio,
                HorarioModel.hora_fin,
            )
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == HorarioModel.id_asignacion)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_detalle == AsignacionMateriaModel.id_detalle)
            .join(SemestreModel,
                  SemestreModel.id_semestre == DetalleSemestreModel.id_semestre)
            .join(DocenteModel,
                  DocenteModel.id_docente == HorarioModel.id_docente)
            .join(AulaModel,
                  AulaModel.id_aula == HorarioModel.id_aula)
            .join(PeriodoEscolarModel,
                  PeriodoEscolarModel.id_periodo == PlanGeneradoModel.id_periodo)
            .filter(PlanGeneradoModel.id_plan == id_plan)
            .order_by(HorarioModel.id_horario)
            .all()
        )

    # ── Escritura ─────────────────────────────────────────────

    def obtener_o_crear_plan_generado(
        self, id_plan: int, id_periodo: int
    ) -> PlanGeneradoModel:
        pg = (
            self._s.query(PlanGeneradoModel)
            .filter_by(id_plan=id_plan, id_periodo=id_periodo)
            .first()
        )
        if pg is None:
            pg = PlanGeneradoModel(id_plan=id_plan, id_periodo=id_periodo)
            self._s.add(pg)
            self._s.flush()
        return pg

    def crear_horario(
        self,
        id_plan_generado: int,
        id_asignacion: int,
        id_docente: int,
        id_aula: int,
        dia: str,
        hora_inicio,
        hora_fin,
        total_horas: int,
    ) -> HorarioModel:
        h = HorarioModel(
            id_plan_generado=id_plan_generado,
            id_asignacion=id_asignacion,
            id_docente=id_docente,
            id_aula=id_aula,
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            total_horas=total_horas,
        )
        self._s.add(h)
        self._s.flush()
        return h

    def eliminar_horario(self, id_horario: int) -> None:
        h = self._s.query(HorarioModel).get(id_horario)
        if h:
            self._s.delete(h)

    # ── Creación de catálogos globales ────────────────────────

    def crear_aula(self, nombre: str) -> AulaModel:
        aula = AulaModel(nombre=nombre)
        self._s.add(aula)
        self._s.flush()
        return aula

    def crear_docente(self, nombre: str) -> DocenteModel:
        docente = DocenteModel(nombre=nombre)
        self._s.add(docente)
        self._s.flush()
        return docente

    def crear_periodo(self, nombre: str) -> PeriodoEscolarModel:
        periodo = PeriodoEscolarModel(nombre=nombre)
        self._s.add(periodo)
        self._s.flush()
        return periodo

    def commit(self)   -> None: self._s.commit()
    def rollback(self) -> None: self._s.rollback()
