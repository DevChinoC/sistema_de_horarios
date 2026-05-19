from sqlalchemy.orm import Session
from sqlalchemy import func
from infrastructure.db.models import (
    PlanEstudiosModel, LiesModel, SemestreModel, NivelAcademicoModel,
    DetalleSemestreModel, AsignacionMateriaModel,
    MateriaTroncoModel, OptativaModel,
    DocenteModel, AulaModel, PeriodoEscolarModel,
    HorarioModel, DetalleHorarioModel, PlanGeneradoModel, TipoMateriaModel,
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
                DetalleHorarioModel.total_horas,
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
            )
            .join(DetalleHorarioModel,
                  DetalleHorarioModel.id_horario == HorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
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

    def obtener_horarios_filtrados(
        self,
        id_plan: int,
        id_lies: int,
        id_semestre: int,
        id_semestre_opt: int | None = None,
    ) -> list[tuple]:
        """Retorna horarios filtrados por LIES y semestre.

        Incluye automáticamente las optativas (semestre con numero=0)
        si se proporciona ``id_semestre_opt``.
        """
        from sqlalchemy import or_

        sem_filter = [DetalleSemestreModel.id_semestre == id_semestre]
        if id_semestre_opt is not None:
            sem_filter.append(DetalleSemestreModel.id_semestre == id_semestre_opt)

        return (
            self._s.query(
                HorarioModel.id_horario,
                SemestreModel.numero.label("semestre"),
                DetalleSemestreModel.nombre_posicion.label("unidad"),
                DocenteModel.nombre.label("docente"),
                AulaModel.nombre.label("aula"),
                PeriodoEscolarModel.nombre.label("periodo"),
                DetalleHorarioModel.total_horas,
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
            )
            .join(DetalleHorarioModel,
                  DetalleHorarioModel.id_horario == HorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
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
            .filter(
                PlanGeneradoModel.id_plan == id_plan,
                DetalleSemestreModel.id_lies == id_lies,
                or_(*sem_filter),
            )
            .order_by(HorarioModel.id_horario)
            .all()
        )

    # ── Escritura ─────────────────────────────────────────────

    def obtener_o_crear_plan_generado(
        self, id_plan: int, id_periodo: int, id_lies: int | None = None,
    ) -> PlanGeneradoModel:
        filters = {"id_plan": id_plan, "id_periodo": id_periodo}
        if id_lies is not None:
            filters["id_lies"] = id_lies
        pg = (
            self._s.query(PlanGeneradoModel)
            .filter_by(**filters)
            .first()
        )
        if pg is None:
            pg = PlanGeneradoModel(
                id_plan=id_plan, id_periodo=id_periodo, id_lies=id_lies)
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
        id_semestre: int | None = None,
    ) -> HorarioModel:
        h = HorarioModel(
            id_plan_generado=id_plan_generado,
            id_docente=id_docente,
            id_aula=id_aula,
            total_horas=total_horas,
        )
        self._s.add(h)
        self._s.flush()
        d = DetalleHorarioModel(
            id_horario=h.id_horario,
            id_asignacion=id_asignacion,
            id_semestre=id_semestre,
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            total_horas=total_horas,
        )
        self._s.add(d)
        self._s.flush()
        return h

    def eliminar_horario(self, id_horario: int) -> None:
        h = self._s.query(HorarioModel).get(id_horario)
        if h:
            # cascade="all, delete-orphan" handles detalles
            self._s.delete(h)

    def obtener_horario_por_id(self, id_horario: int) -> tuple | None:
        """Retorna los IDs y datos del PRIMER detalle para pre-poblar el formulario."""
        return (
            self._s.query(
                HorarioModel.id_horario,
                DetalleHorarioModel.id_asignacion,
                DetalleSemestreModel.id_semestre,
                HorarioModel.id_docente,
                HorarioModel.id_aula,
                PlanGeneradoModel.id_periodo,
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
                DetalleHorarioModel.total_horas,
                PeriodoEscolarModel.nombre.label("periodo_nombre"),
            )
            .join(DetalleHorarioModel,
                  DetalleHorarioModel.id_horario == HorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
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
        id_semestre: int | None = None,
    ) -> None:
        h = self._s.query(HorarioModel).get(id_horario)
        if h:
            h.id_docente    = id_docente
            h.id_aula       = id_aula
            h.total_horas   = total_horas
            # Si cambia el periodo, actualizar plan_generado
            pg = h.plan_generado
            if pg.id_periodo != id_periodo:
                new_pg = self.obtener_o_crear_plan_generado(
                    pg.id_plan, id_periodo, pg.id_lies)
                h.id_plan_generado = new_pg.id_plan_generado
            # Reemplazar detalles: eliminar todos y crear uno nuevo
            for det in list(h.detalles):
                self._s.delete(det)
            self._s.flush()
            d = DetalleHorarioModel(
                id_horario=h.id_horario,
                id_asignacion=id_asignacion,
                id_semestre=id_semestre,
                dia=dia,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                total_horas=total_horas,
            )
            self._s.add(d)
            self._s.flush()

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

        Filtra por ``DetalleHorarioModel.id_semestre`` (el semestre real
        seleccionado al crear el horario), no por el semestre de la
        estructura del plan.
        """
        q = (
            self._s.query(
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
                DetalleSemestreModel.nombre_posicion.label("materia"),
                LiesModel.nombre.label("lies_nombre"),
            )
            .join(HorarioModel,
                  HorarioModel.id_horario == DetalleHorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_detalle == AsignacionMateriaModel.id_detalle)
            .join(LiesModel,
                  LiesModel.id_lies == DetalleSemestreModel.id_lies)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanGeneradoModel.id_plan == id_plan,
                PlanGeneradoModel.id_periodo == id_periodo,
            )
        )
        if id_semestre is not None:
            q = q.filter(DetalleHorarioModel.id_semestre == id_semestre)

        return q.distinct().order_by(DetalleHorarioModel.hora_inicio, DetalleHorarioModel.dia).all()

    # ── Filtros en cascada para vista Horario Docente ────────

    def obtener_periodos_por_docente(
        self, id_docente: int,
    ) -> list[PeriodoEscolarModel]:
        """Periodos donde el docente tiene al menos un horario registrado."""
        id_list = [
            r[0] for r in
            self._s.query(PeriodoEscolarModel.id_periodo)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_periodo == PeriodoEscolarModel.id_periodo)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .filter(HorarioModel.id_docente == id_docente)
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(PeriodoEscolarModel)
            .filter(PeriodoEscolarModel.id_periodo.in_(id_list))
            .order_by(PeriodoEscolarModel.nombre)
            .all()
        )

    def obtener_planes_por_docente_periodo(
        self, id_docente: int, id_periodo: int,
    ) -> list[PlanEstudiosModel]:
        """Planes donde el docente tiene horarios en el periodo dado."""
        id_list = [
            r[0] for r in
            self._s.query(PlanGeneradoModel.id_plan)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanGeneradoModel.id_periodo == id_periodo,
            )
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(PlanEstudiosModel)
            .filter(PlanEstudiosModel.id_plan.in_(id_list))
            .order_by(PlanEstudiosModel.nombre)
            .all()
        )

    def obtener_semestres_por_docente_plan_periodo(
        self, id_docente: int, id_plan: int, id_periodo: int,
    ) -> list[SemestreModel]:
        """Semestres donde el docente tiene horarios.

        Usa ``DetalleHorarioModel.id_semestre`` (el semestre real guardado
        al crear el horario) para determinar los semestres disponibles.
        """
        id_list = [
            r[0] for r in
            self._s.query(DetalleHorarioModel.id_semestre)
            .join(HorarioModel,
                  HorarioModel.id_horario == DetalleHorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanGeneradoModel.id_plan == id_plan,
                PlanGeneradoModel.id_periodo == id_periodo,
                DetalleHorarioModel.id_semestre.isnot(None),
            )
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        return (
            self._s.query(SemestreModel)
            .filter(
                SemestreModel.id_semestre.in_(id_list),
                SemestreModel.numero > 0,
            )
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

    # ── Cascada por Grado (nivel) ─────────────────────────────

    def obtener_niveles_con_historial(self) -> list[NivelAcademicoModel]:
        """Retorna niveles que tienen al menos un plan_generado en historial."""
        id_list = [
            r[0] for r in
            self._s.query(PlanEstudiosModel.id_nivel)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan == PlanEstudiosModel.id_plan)
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(NivelAcademicoModel)
            .filter(NivelAcademicoModel.id_nivel.in_(id_list))
            .order_by(NivelAcademicoModel.nombre)
            .all()
        )

    def obtener_periodos_por_nivel(
        self, id_nivel: int,
    ) -> list[PeriodoEscolarModel]:
        """Periodos que tienen al menos un plan_generado del nivel dado."""
        id_list = [
            r[0] for r in
            self._s.query(PlanGeneradoModel.id_periodo)
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .filter(PlanEstudiosModel.id_nivel == id_nivel)
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(PeriodoEscolarModel)
            .filter(PeriodoEscolarModel.id_periodo.in_(id_list))
            .order_by(PeriodoEscolarModel.nombre)
            .all()
        )

    def obtener_planes_por_nivel_periodo(
        self, id_nivel: int, id_periodo: int,
    ) -> list[PlanEstudiosModel]:
        """Planes activos del nivel que tienen plan_generado en el periodo."""
        id_list = [
            r[0] for r in
            self._s.query(PlanGeneradoModel.id_plan)
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .filter(
                PlanEstudiosModel.id_nivel == id_nivel,
                PlanGeneradoModel.id_periodo == id_periodo,
            )
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(PlanEstudiosModel)
            .filter(PlanEstudiosModel.id_plan.in_(id_list))
            .order_by(PlanEstudiosModel.nombre)
            .all()
        )

    def obtener_semestres_por_nivel_plan_periodo(
        self, id_nivel: int, id_plan: int, id_periodo: int,
    ) -> list[SemestreModel]:
        """Semestres (numero > 0) del plan/nivel/periodo con horarios."""
        id_list = [
            r[0] for r in
            self._s.query(SemestreModel.id_semestre)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_semestre == SemestreModel.id_semestre)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_detalle == DetalleSemestreModel.id_detalle)
            .join(DetalleHorarioModel,
                  DetalleHorarioModel.id_asignacion == AsignacionMateriaModel.id_asignacion)
            .join(HorarioModel,
                  HorarioModel.id_horario == DetalleHorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .filter(
                PlanEstudiosModel.id_nivel == id_nivel,
                PlanGeneradoModel.id_plan == id_plan,
                PlanGeneradoModel.id_periodo == id_periodo,
                SemestreModel.numero > 0,
            )
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(SemestreModel)
            .filter(SemestreModel.id_semestre.in_(id_list))
            .order_by(SemestreModel.numero)
            .all()
        )

    def obtener_niveles_con_docente(self) -> list[NivelAcademicoModel]:
        """Retorna niveles que tienen planes con horarios de docentes."""
        id_list = [
            r[0] for r in
            self._s.query(PlanEstudiosModel.id_nivel)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan == PlanEstudiosModel.id_plan)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(NivelAcademicoModel)
            .filter(NivelAcademicoModel.id_nivel.in_(id_list))
            .order_by(NivelAcademicoModel.nombre)
            .all()
        )

    def obtener_periodos_por_docente_nivel(
        self, id_docente: int, id_nivel: int,
    ) -> list[PeriodoEscolarModel]:
        """Periodos donde el docente tiene horarios en planes del nivel dado."""
        id_list = [
            r[0] for r in
            self._s.query(PeriodoEscolarModel.id_periodo)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_periodo == PeriodoEscolarModel.id_periodo)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanEstudiosModel.id_nivel == id_nivel,
            )
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(PeriodoEscolarModel)
            .filter(PeriodoEscolarModel.id_periodo.in_(id_list))
            .order_by(PeriodoEscolarModel.nombre)
            .all()
        )

    def obtener_planes_por_docente_nivel_periodo(
        self, id_docente: int, id_nivel: int, id_periodo: int,
    ) -> list[PlanEstudiosModel]:
        """Planes del nivel/periodo donde el docente tiene horarios."""
        id_list = [
            r[0] for r in
            self._s.query(PlanGeneradoModel.id_plan)
            .join(HorarioModel,
                  HorarioModel.id_plan_generado == PlanGeneradoModel.id_plan_generado)
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .filter(
                HorarioModel.id_docente == id_docente,
                PlanEstudiosModel.id_nivel == id_nivel,
                PlanGeneradoModel.id_periodo == id_periodo,
            )
            .distinct()
            .all()
        ]
        if not id_list:
            return []
        id_list = list(dict.fromkeys(id_list))  # deduplicar
        return (
            self._s.query(PlanEstudiosModel)
            .filter(PlanEstudiosModel.id_plan.in_(id_list))
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
        """Obtiene un periodo existente por nombre, o lo crea si no existe."""
        existente = (
            self._s.query(PeriodoEscolarModel)
            .filter(PeriodoEscolarModel.nombre == nombre)
            .first()
        )
        if existente:
            return existente
        periodo = PeriodoEscolarModel(nombre=nombre)
        self._s.add(periodo)
        self._s.flush()
        return periodo


    def obtener_historial_planes(self) -> list[tuple]:
        """Retorna todos los planes_generados con info de plan, nivel, periodo y LIES."""
        return (
            self._s.query(
                PlanGeneradoModel.id_plan_generado,
                PlanEstudiosModel.nombre.label("nombre_plan"),
                NivelAcademicoModel.nombre.label("nombre_nivel"),
                PeriodoEscolarModel.nombre.label("nombre_periodo"),
                LiesModel.nombre.label("nombre_lies"),
            )
            .join(PlanEstudiosModel,
                  PlanEstudiosModel.id_plan == PlanGeneradoModel.id_plan)
            .join(NivelAcademicoModel,
                  NivelAcademicoModel.id_nivel == PlanEstudiosModel.id_nivel)
            .join(PeriodoEscolarModel,
                  PeriodoEscolarModel.id_periodo == PlanGeneradoModel.id_periodo)
            .outerjoin(LiesModel,
                       LiesModel.id_lies == PlanGeneradoModel.id_lies)
            .order_by(PlanGeneradoModel.id_plan_generado.desc())
            .all()
        )

    def obtener_horarios_de_plan_generado(self, id_plan_generado: int) -> list[tuple]:
        """Retorna horarios de un plan_generado con info para la tabla de edición."""
        return (
            self._s.query(
                HorarioModel.id_horario,
                SemestreModel.numero.label("semestre"),
                DetalleSemestreModel.nombre_posicion.label("unidad"),
                DocenteModel.nombre.label("docente"),
                AulaModel.nombre.label("aula"),
                PeriodoEscolarModel.nombre.label("periodo"),
                DetalleHorarioModel.total_horas,
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
            )
            .join(DetalleHorarioModel,
                  DetalleHorarioModel.id_horario == HorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
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
            .filter(HorarioModel.id_plan_generado == id_plan_generado)
            .order_by(HorarioModel.id_horario)
            .all()
        )

    def eliminar_plan_generado(self, id_plan_generado: int) -> None:
        """Elimina todos los horarios (con detalles via cascade) y el plan_generado."""
        horarios = self._s.query(HorarioModel).filter_by(
            id_plan_generado=id_plan_generado).all()
        for h in horarios:
            self._s.delete(h)  # cascade deletes detalles
        pg = self._s.query(PlanGeneradoModel).get(id_plan_generado)
        if pg:
            self._s.delete(pg)
        self._s.flush()

    # ── Validación tronco común entre LIES ────────────────────

    def obtener_horario_tronco_existente(
        self,
        id_plan: int,
        id_materia: int,
        excluir_id_asignacion: int | None = None,
    ) -> list[tuple]:
        """Busca horarios ya registrados para la misma materia de tronco
        (id_materia) en *cualquier* LIES del mismo plan.

        Retorna lista de (dia, hora_inicio, hora_fin, lies_nombre).
        Se puede excluir un id_asignacion específico (útil al editar).
        """
        q = (
            self._s.query(
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
                LiesModel.nombre.label("lies_nombre"),
            )
            .join(HorarioModel,
                  HorarioModel.id_horario == DetalleHorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_detalle == AsignacionMateriaModel.id_detalle)
            .join(LiesModel,
                  LiesModel.id_lies == DetalleSemestreModel.id_lies)
            .filter(
                PlanGeneradoModel.id_plan == id_plan,
                AsignacionMateriaModel.id_materia == id_materia,
            )
        )
        if excluir_id_asignacion is not None:
            q = q.filter(
                AsignacionMateriaModel.id_asignacion != excluir_id_asignacion)
        return q.all()

    def obtener_id_materia_de_asignacion(
        self, id_asignacion: int,
    ) -> int | None:
        """Retorna el id_materia (tronco) de una asignación, o None si es optativa."""
        asig = self._s.query(AsignacionMateriaModel).get(id_asignacion)
        return asig.id_materia if asig else None

    def obtener_horarios_tronco_del_plan(
        self, id_plan: int,
    ) -> list[tuple]:
        """Retorna todos los horarios de materias de tronco común del plan.

        Retorna (dia, hora_inicio, hora_fin, nombre_materia).
        Se usa para verificar que una optativa no ocupe el mismo bloque.
        """
        return (
            self._s.query(
                DetalleHorarioModel.dia,
                DetalleHorarioModel.hora_inicio,
                DetalleHorarioModel.hora_fin,
                DetalleSemestreModel.nombre_posicion.label("nombre_materia"),
            )
            .join(HorarioModel,
                  HorarioModel.id_horario == DetalleHorarioModel.id_horario)
            .join(PlanGeneradoModel,
                  PlanGeneradoModel.id_plan_generado == HorarioModel.id_plan_generado)
            .join(AsignacionMateriaModel,
                  AsignacionMateriaModel.id_asignacion == DetalleHorarioModel.id_asignacion)
            .join(DetalleSemestreModel,
                  DetalleSemestreModel.id_detalle == AsignacionMateriaModel.id_detalle)
            .filter(
                PlanGeneradoModel.id_plan == id_plan,
                AsignacionMateriaModel.id_materia.isnot(None),
            )
            .all()
        )

    def commit(self)   -> None: self._s.commit()
    def rollback(self) -> None: self._s.rollback()