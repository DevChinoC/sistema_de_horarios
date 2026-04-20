from sqlalchemy.orm import Session
from sqlalchemy import func
from infrastructure.db.models import (
    PlanEstudiosModel, LiesModel, SemestreModel, NivelAcademicoModel,
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

    def obtener_horario_por_id(self, id_horario: int) -> tuple | None:
        """Retorna los IDs y datos necesarios para pre-poblar el formulario de edición."""
        return (
            self._s.query(
                HorarioModel.id_horario,
                HorarioModel.id_asignacion,
                DetalleSemestreModel.id_semestre,
                HorarioModel.id_docente,
                HorarioModel.id_aula,
                PlanGeneradoModel.id_periodo,
                HorarioModel.dia,
                HorarioModel.hora_inicio,
                HorarioModel.hora_fin,
                HorarioModel.total_horas,
                PeriodoEscolarModel.nombre.label("periodo_nombre"),
            )
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == HorarioModel.id_asignacion)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_detalle == AsignacionMateriaModel.id_detalle)
            .join(PeriodoEscolarModel,
                  PeriodoEscolarModel.id_periodo == PlanGeneradoModel.id_periodo)
            .filter(HorarioModel.id_horario == id_horario)
            .first()
        )

    def actualizar_horario(
        self,
        id_horario: int,
        id_asignacion: int,
        id_docente: int,
        id_aula: int,
        id_periodo: int,
        dia: str,
        hora_inicio,
        hora_fin,
        total_horas: int,
    ) -> None:
        h = self._s.query(HorarioModel).get(id_horario)
        if h:
            h.id_asignacion = id_asignacion
            h.id_docente    = id_docente
            h.id_aula       = id_aula
            h.dia           = dia
            h.hora_inicio   = hora_inicio
            h.hora_fin      = hora_fin
            h.total_horas   = total_horas
            # Si cambia el periodo, actualizar plan_generado
            pg = h.plan_generado
            if pg.id_periodo != id_periodo:
                new_pg = self.obtener_o_crear_plan_generado(pg.id_plan, id_periodo)
                h.id_plan_generado = new_pg.id_plan_generado

    # ── Horarios por docente (vista Horario Docente) ─────────

    def obtener_horarios_por_docente(
        self,
        id_docente: int,
        id_plan: int,
        id_periodo: int,
        id_semestre: int | None = None,
    ) -> list[tuple]:
        """Retorna filas (dia, hora_inicio, hora_fin, materia, lies_nombre)
        del docente en un plan/periodo dados, opcionalmente filtrado por semestre.
        """
        q = (
            self._s.query(
                HorarioModel.dia,
                HorarioModel.hora_inicio,
                HorarioModel.hora_fin,
                DetalleSemestreModel.nombre_posicion.label("materia"),
                LiesModel.nombre.label("lies_nombre"),
            )
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == HorarioModel.id_asignacion)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_detalle == AsignacionMateriaModel.id_detalle)
            .join(SemestreModel,
                  SemestreModel.id_semestre == DetalleSemestreModel.id_semestre)
            .join(LiesModel,
                  LiesModel.id_lies == DetalleSemestreModel.id_lies)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanGeneradoModel.id_plan == id_plan,
                PlanGeneradoModel.id_periodo == id_periodo,
            )
        )
        if id_semestre is not None:
            q = q.filter(DetalleSemestreModel.id_semestre == id_semestre)

        return q.order_by(HorarioModel.hora_inicio, HorarioModel.dia).all()

    # ── Filtros en cascada para vista Horario Docente ────────

    def obtener_periodos_por_docente(
        self, id_docente: int,
    ) -> list[PeriodoEscolarModel]:
        """Periodos donde el docente tiene al menos un horario registrado."""
        ids = (
            self._s.query(PeriodoEscolarModel.id_periodo)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_periodo == PeriodoEscolarModel.id_periodo)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .filter(HorarioModel.id_docente == id_docente)
            .distinct()
            .scalar_subquery()
        )
        return (
            self._s.query(PeriodoEscolarModel)
            .filter(PeriodoEscolarModel.id_periodo.in_(ids))
            .order_by(PeriodoEscolarModel.nombre)
            .all()
        )

    def obtener_planes_por_docente_periodo(
        self, id_docente: int, id_periodo: int,
    ) -> list[PlanEstudiosModel]:
        """Planes donde el docente tiene horarios en el periodo dado."""
        ids = (
            self._s.query(PlanGeneradoModel.id_plan)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanGeneradoModel.id_periodo == id_periodo,
            )
            .distinct()
            .scalar_subquery()
        )
        return (
            self._s.query(PlanEstudiosModel)
            .filter(PlanEstudiosModel.id_plan.in_(ids))
            .order_by(PlanEstudiosModel.nombre)
            .all()
        )

    def obtener_semestres_por_docente_plan_periodo(
        self, id_docente: int, id_plan: int, id_periodo: int,
    ) -> list[SemestreModel]:
        """Semestres (numero > 0) donde el docente tiene horarios."""
        ids = (
            self._s.query(SemestreModel.id_semestre)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_semestre == SemestreModel.id_semestre)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_detalle == DetalleSemestreModel.id_detalle)
            .join(HorarioModel,
                  HorarioModel.id_asignacion == AsignacionMateriaModel.id_asignacion)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanGeneradoModel.id_plan == id_plan,
                PlanGeneradoModel.id_periodo == id_periodo,
                SemestreModel.numero > 0,
            )
            .distinct()
            .scalar_subquery()
        )
        return (
            self._s.query(SemestreModel)
            .filter(SemestreModel.id_semestre.in_(ids))
            .order_by(SemestreModel.numero)
            .all()
        )

    def obtener_planes_activos(self) -> list[PlanEstudiosModel]:
        """Retorna todos los planes de estudio activos."""
        return (
            self._s.query(PlanEstudiosModel)
            .filter_by(activo=1)
            .order_by(PlanEstudiosModel.nombre)
            .all()
        )

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


    def obtener_historial_planes(self) -> list[tuple]:
        """Retorna todos los planes_generados con info de plan, nivel y periodo."""
        return (
            self._s.query(
                PlanGeneradoModel.id_plan_generado,
                PlanEstudiosModel.nombre.label("nombre_plan"),
                NivelAcademicoModel.nombre.label("nombre_nivel"),
                PeriodoEscolarModel.nombre.label("nombre_periodo"),
            )
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .join(NivelAcademicoModel,
                  NivelAcademicoModel.id_nivel == PlanEstudiosModel.id_nivel)
            .join(PeriodoEscolarModel,
                  PeriodoEscolarModel.id_periodo == PlanGeneradoModel.id_periodo)
            .order_by(PlanGeneradoModel.id_plan_generado.desc())
            .all()
        )

    def eliminar_plan_generado(self, id_plan_generado: int) -> None:
        """Elimina todos los horarios de un plan_generado y luego el plan_generado."""
        self._s.query(HorarioModel).filter_by(
            id_plan_generado=id_plan_generado).delete()
        pg = self._s.query(PlanGeneradoModel).get(id_plan_generado)
        if pg:
            self._s.delete(pg)
        self._s.flush()

    def commit(self)   -> None: self._s.commit()
    def rollback(self) -> None: self._s.rollback()
