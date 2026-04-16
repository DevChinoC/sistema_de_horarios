from datetime import datetime, time as dtime

from application.dto.horario_dto import (
    LiesDTO, SemestreDTO, UnidadAprendizajeDTO,
    DocenteDTO, AulaDTO, PeriodoDTO,
    HorarioRegistradoDTO, GuardarHorarioDTO, HorarioDetalleDTO,
)
from application.dto.horario_docente_dto import (
    HorarioDocenteFilaDTO, HorarioDocenteResumenDTO,
)
from application.dto.planes_dto import PlanDTO
from infrastructure.db.connection import DatabaseConnection
from infrastructure.repositories.horario_repository import HorarioRepository


class HorarioService:
    """Casos de uso para la vista de detalle de plan y registro de horarios."""

    # Nombre exacto en BD del nivel que tiene LIES múltiples
    NIVEL_CON_LIES = "MIIDT"

    def __init__(self) -> None:
        self._db = DatabaseConnection()

    # ── Datos del plan ────────────────────────────────────────

    def obtener_nombre_plan(self, id_plan: int) -> str:
        session = self._db.get_session()
        try:
            repo = HorarioRepository(session)
            plan = repo.obtener_plan(id_plan)
            return plan.nombre if plan else ""
        finally:
            session.close()

    def obtener_nombre_nivel(self, id_plan: int) -> str:
        session = self._db.get_session()
        try:
            repo = HorarioRepository(session)
            plan = repo.obtener_plan(id_plan)
            return plan.nivel.nombre if plan else ""
        finally:
            session.close()

    # ── LIES del plan ─────────────────────────────────────────

    def obtener_lies_del_plan(self, id_plan: int) -> list[LiesDTO]:
        """Solo retorna LIES si el nivel es MIIDT; si no, lista vacía."""
        session = self._db.get_session()
        try:
            repo  = HorarioRepository(session)
            plan  = repo.obtener_plan(id_plan)
            if not plan:
                return []
            # Solo MIIDT tiene LIES múltiples
            if plan.nivel.nombre.upper() != self.NIVEL_CON_LIES.upper():
                return []
            return [LiesDTO(id=l.id_lies, nombre=l.nombre)
                    for l in repo.obtener_lies_del_plan(id_plan)]
        finally:
            session.close()

    def obtener_todas_lies_del_plan(self, id_plan: int) -> list[LiesDTO]:
        """Retorna TODAS las lies asociadas al plan, sin importar el nivel."""
        session = self._db.get_session()
        try:
            repo = HorarioRepository(session)
            return [LiesDTO(id=l.id_lies, nombre=l.nombre)
                    for l in repo.obtener_lies_del_plan(id_plan)]
        finally:
            session.close()

    # ── Semestres ─────────────────────────────────────────────

    def obtener_semestres(self, id_plan: int) -> list[SemestreDTO]:
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_semestres(id_plan)
            return [SemestreDTO(id=r.id_semestre, numero=r.numero) for r in rows]
        finally:
            session.close()

    # ── Unidades de aprendizaje ───────────────────────────────

    def obtener_unidades(
        self,
        id_plan: int,
        id_lies: int,
        id_semestre: int | None = None,
    ) -> list[UnidadAprendizajeDTO]:
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_unidades(
                id_plan, id_lies, id_semestre
            )
            return [
                UnidadAprendizajeDTO(
                    id_detalle=r.id_detalle,
                    id_asignacion=r.id_asignacion,
                    nombre=r.nombre_posicion or "",
                    tipo=r.tipo,
                    numero_semestre=r.numero_semestre,
                    id_lies=id_lies,
                )
                for r in rows
            ]
        finally:
            session.close()

    # ── Catálogos ─────────────────────────────────────────────

    def obtener_docentes(self) -> list[DocenteDTO]:
        session = self._db.get_session()
        try:
            return [DocenteDTO(id=d.id_docente, nombre=d.nombre)
                    for d in HorarioRepository(session).obtener_docentes()]
        finally:
            session.close()

    def obtener_aulas(self) -> list[AulaDTO]:
        session = self._db.get_session()
        try:
            return [AulaDTO(id=a.id_aula, nombre=a.nombre)
                    for a in HorarioRepository(session).obtener_aulas()]
        finally:
            session.close()

    def obtener_periodos(self) -> list[PeriodoDTO]:
        session = self._db.get_session()
        try:
            return [PeriodoDTO(id=p.id_periodo, nombre=p.nombre)
                    for p in HorarioRepository(session).obtener_periodos()]
        finally:
            session.close()

    def obtener_tipos_materia(self) -> list[dict]:
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_tipos_materia()
            return [{"id": t.id_tipo, "nombre": t.nombre} for t in rows]
        finally:
            session.close()

    # ── Horarios registrados ──────────────────────────────────

    def obtener_horarios(self, id_plan: int) -> list[HorarioRegistradoDTO]:
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_horarios_del_plan(id_plan)
            result = []
            for idx, r in enumerate(rows, start=1):
                result.append(HorarioRegistradoDTO(
                    id_horario=r.id_horario,
                    clave=str(idx).zfill(3),
                    semestre=f"Semestre {r.semestre}" if r.semestre > 0 else "Optativa",
                    unidad=r.unidad or "",
                    docente=r.docente or "",
                    aulas=r.aula or "",
                    periodo=r.periodo or "",
                    total_horas=r.total_horas or 0,
                    dia=r.dia or "",
                    hora_inicio=r.hora_inicio.strftime("%H:%M") if r.hora_inicio else "",
                    hora_fin=r.hora_fin.strftime("%H:%M") if r.hora_fin else "",
                    numero_semestre=r.semestre if r.semestre else 0,
                ))
            return result
        finally:
            session.close()

    # ── Guardar horario ───────────────────────────────────────

    def guardar_horario(self, dto: GuardarHorarioDTO) -> tuple[bool, str]:
        session = self._db.get_session()
        repo    = HorarioRepository(session)
        try:
            # Parsear horas
            hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
            hf = datetime.strptime(dto.hora_fin,    "%H:%M").time()

            pg = repo.obtener_o_crear_plan_generado(dto.id_plan, dto.id_periodo)
            repo.crear_horario(
                id_plan_generado=pg.id_plan_generado,
                id_asignacion=dto.id_asignacion,
                id_docente=dto.id_docente,
                id_aula=dto.id_aula,
                dia=dto.dia,
                hora_inicio=hi,
                hora_fin=hf,
                total_horas=dto.total_horas,
            )
            repo.commit()
            return True, "Horario guardado correctamente."
        except Exception as e:
            repo.rollback()
            return False, f"Error al guardar horario: {e}"
        finally:
            session.close()

    # ── Eliminar horario ──────────────────────────────────────

    def eliminar_horario(self, id_horario: int) -> tuple[bool, str]:
        session = self._db.get_session()
        repo    = HorarioRepository(session)
        try:
            repo.eliminar_horario(id_horario)
            repo.commit()
            return True, "Horario eliminado."
        except Exception as e:
            repo.rollback()
            return False, f"Error al eliminar: {e}"
        finally:
            session.close()

    # ── Obtener detalle de horario (para edición) ──────────────

    def obtener_horario_detalle(self, id_horario: int) -> HorarioDetalleDTO | None:
        session = self._db.get_session()
        try:
            r = HorarioRepository(session).obtener_horario_por_id(id_horario)
            if r is None:
                return None
            return HorarioDetalleDTO(
                id_horario=r.id_horario,
                id_asignacion=r.id_asignacion,
                id_semestre=r.id_semestre,
                id_docente=r.id_docente,
                id_aula=r.id_aula,
                id_periodo=r.id_periodo,
                dia=r.dia or "",
                hora_inicio=r.hora_inicio.strftime("%H:%M") if r.hora_inicio else "",
                hora_fin=r.hora_fin.strftime("%H:%M") if r.hora_fin else "",
                total_horas=r.total_horas or 0,
                periodo_nombre=r.periodo_nombre or "",
            )
        finally:
            session.close()

    # ── Actualizar horario existente ────────────────────────

    def actualizar_horario(
        self,
        id_horario: int,
        dto: GuardarHorarioDTO,
    ) -> tuple[bool, str]:
        session = self._db.get_session()
        repo    = HorarioRepository(session)
        try:
            hi = datetime.strptime(dto.hora_inicio, "%H:%M").time()
            hf = datetime.strptime(dto.hora_fin,    "%H:%M").time()
            repo.actualizar_horario(
                id_horario=id_horario,
                id_asignacion=dto.id_asignacion,
                id_docente=dto.id_docente,
                id_aula=dto.id_aula,
                id_periodo=dto.id_periodo,
                dia=dto.dia,
                hora_inicio=hi,
                hora_fin=hf,
                total_horas=dto.total_horas,
            )
            repo.commit()
            return True, "Horario actualizado correctamente."
        except Exception as e:
            repo.rollback()
            return False, f"Error al actualizar horario: {e}"
        finally:
            session.close()

    # ── Creación de catálogos globales ────────────────────────

    def crear_aula(self, nombre: str) -> AulaDTO | None:
        session = self._db.get_session()
        repo    = HorarioRepository(session)
        try:
            aula = repo.crear_aula(nombre)
            repo.commit()
            return AulaDTO(id=aula.id_aula, nombre=aula.nombre)
        except Exception:
            repo.rollback()
            return None
        finally:
            session.close()

    def crear_docente(self, nombre: str) -> DocenteDTO | None:
        session = self._db.get_session()
        repo    = HorarioRepository(session)
        try:
            doc = repo.crear_docente(nombre)
            repo.commit()
            return DocenteDTO(id=doc.id_docente, nombre=doc.nombre)
        except Exception:
            repo.rollback()
            return None
        finally:
            session.close()

    def crear_periodo(self, nombre: str) -> PeriodoDTO | None:
        session = self._db.get_session()
        repo    = HorarioRepository(session)
        try:
            per = repo.crear_periodo(nombre)
            repo.commit()
            return PeriodoDTO(id=per.id_periodo, nombre=per.nombre)
        except Exception:
            repo.rollback()
            return None
        finally:
            session.close()

    # ══════════════════════════════════════════════════════════
    # Horario por Docente — nuevos métodos
    # ══════════════════════════════════════════════════════════

    # ── Filtros en cascada ────────────────────────────────────

    def obtener_periodos_por_docente(self, id_docente: int) -> list[PeriodoDTO]:
        """Periodos donde el docente tiene horarios registrados."""
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_periodos_por_docente(id_docente)
            return [PeriodoDTO(id=p.id_periodo, nombre=p.nombre) for p in rows]
        finally:
            session.close()

    def obtener_planes_por_docente_periodo(
        self, id_docente: int, id_periodo: int,
    ) -> list[PlanDTO]:
        """Planes donde el docente tiene horarios en el periodo dado."""
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_planes_por_docente_periodo(
                id_docente, id_periodo)
            return [PlanDTO(id=p.id_plan, nombre=p.nombre, id_nivel=p.id_nivel)
                    for p in rows]
        finally:
            session.close()

    def obtener_semestres_por_docente_plan_periodo(
        self, id_docente: int, id_plan: int, id_periodo: int,
    ) -> list[SemestreDTO]:
        """Semestres donde el docente tiene horarios (numero > 0)."""
        session = self._db.get_session()
        try:
            rows = HorarioRepository(session).obtener_semestres_por_docente_plan_periodo(
                id_docente, id_plan, id_periodo)
            return [SemestreDTO(id=s.id_semestre, numero=s.numero) for s in rows]
        finally:
            session.close()

    def obtener_planes_activos(self) -> list[PlanDTO]:
        """Retorna todos los planes de estudio activos para el dropdown."""
        session = self._db.get_session()
        try:
            planes = HorarioRepository(session).obtener_planes_activos()
            return [PlanDTO(id=p.id_plan, nombre=p.nombre, id_nivel=p.id_nivel)
                    for p in planes]
        finally:
            session.close()

    def obtener_nombre_docente(self, id_docente: int) -> str:
        """Retorna el nombre de un docente por su ID."""
        session = self._db.get_session()
        try:
            docs = HorarioRepository(session).obtener_docentes()
            for d in docs:
                if d.id_docente == id_docente:
                    return d.nombre
            return ""
        finally:
            session.close()

    def obtener_horarios_docente(
        self,
        id_docente: int,
        id_plan: int,
        id_periodo: int,
        id_semestre: int | None = None,
    ) -> HorarioDocenteResumenDTO:
        """Obtiene el horario semanal de un docente.

        Si el plan es MIIDT, trae horarios de todas las LIES (sin filtrar
        por semestre específico si id_semestre es None).
        """
        session = self._db.get_session()
        try:
            repo = HorarioRepository(session)
            plan = repo.obtener_plan(id_plan)
            nombre_plan = plan.nombre if plan else ""
            es_miidt = (plan.nivel.nombre.upper() == self.NIVEL_CON_LIES.upper()
                        if plan else False)

            # Para MIIDT no filtramos por semestre — traemos todo
            sem_filter = None if es_miidt else id_semestre

            rows = repo.obtener_horarios_por_docente(
                id_docente=id_docente,
                id_plan=id_plan,
                id_periodo=id_periodo,
                id_semestre=sem_filter,
            )

            filas = []
            for r in rows:
                filas.append(HorarioDocenteFilaDTO(
                    dia=r.dia or "",
                    hora_inicio=(r.hora_inicio.strftime("%H:%M")
                                 if r.hora_inicio else ""),
                    hora_fin=(r.hora_fin.strftime("%H:%M")
                              if r.hora_fin else ""),
                    nombre_materia=r.materia or "",
                    nombre_lies=r.lies_nombre or "",
                ))

            # Obtener nombre del docente
            nombre_docente = self.obtener_nombre_docente(id_docente)

            # Número de semestre
            num_sem = 0
            if id_semestre:
                sems = self.obtener_semestres(id_plan)
                for s in sems:
                    if s.id == id_semestre:
                        num_sem = s.numero
                        break

            return HorarioDocenteResumenDTO(
                nombre_docente=nombre_docente,
                nombre_plan=nombre_plan,
                semestre=num_sem,
                filas=filas,
            )
        finally:
            session.close()

