from datetime import datetime, time as dtime

from application.dto.horario_dto import (
    LiesDTO, SemestreDTO, UnidadAprendizajeDTO,
    DocenteDTO, AulaDTO, PeriodoDTO,
    HorarioRegistradoDTO, GuardarHorarioDTO,
)
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
