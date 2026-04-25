from application.dto.plan_estudios_dto import CrearPlanDTO, FilaMateriaDTO
from domain.models.plan_estudios import PlanEstudiosDomain, FilaMateria
from infrastructure.db.connection import DatabaseConnection
from infrastructure.repositories.plan_estudios_repository import PlanEstudiosRepository
from infrastructure.db.models import MateriaTroncoModel, OptativaModel


class PlanEstudiosService:
    def __init__(self) -> None:
        self._db = DatabaseConnection()

    def obtener_niveles(self) -> list[dict]:
        session = self._db.get_session()
        try:
            return [{"id": n.id_nivel, "nombre": n.nombre}
                    for n in PlanEstudiosRepository(session).obtener_niveles()]
        finally:
            session.close()

    def obtener_lies(self) -> list[dict]:
        session = self._db.get_session()
        try:
            return [{"id": l.id_lies, "nombre": l.nombre}
                    for l in PlanEstudiosRepository(session).obtener_lies()]
        finally:
            session.close()

    def obtener_tipos_materia(self) -> list[dict]:
        session = self._db.get_session()
        try:
            return [{"id": t.id_tipo, "nombre": t.nombre}
                    for t in PlanEstudiosRepository(session).obtener_tipos_materia()]
        finally:
            session.close()

    def obtener_materias_tronco(self) -> list[dict]:
        session = self._db.get_session()
        try:
            return [{"id": m.id_materia, "nombre": m.nombre}
                    for m in PlanEstudiosRepository(session).obtener_materias_tronco()]
        finally:
            session.close()

    def crear_nivel(self, nombre: str) -> dict | None:
        session = self._db.get_session()
        repo = PlanEstudiosRepository(session)
        try:
            nivel = repo.crear_nivel(nombre)
            repo.commit()
            return {"id": nivel.id_nivel, "nombre": nivel.nombre}
        except Exception:
            repo.rollback()
            return None
        finally:
            session.close()

    def crear_plan(self, dto: CrearPlanDTO) -> tuple[bool, str]:
        """Crea un plan asociado a TODAS las LIES.

        - Materias tronco (id_tipo=1): semestres 1-8, se crea detalle
          para CADA LIES y asignación a materias_tronco.
        - Optativas (id_tipo=2, semestre=0): se crean en tabla optativas
          y detalle para CADA LIES con semestre 0.
        """
        dominio = PlanEstudiosDomain(
            nombre=dto.nombre, id_nivel=dto.id_nivel, lies_ids=dto.lies_ids,
            filas=[FilaMateria(f.nombre_materia, f.id_tipo, f.numero_semestre)
                   for f in dto.filas],
        )
        valido, msg = dominio.es_valido()
        if not valido:
            return False, msg

        session = self._db.get_session()
        repo    = PlanEstudiosRepository(session)
        try:
            # Crear plan vinculado a TODAS las LIES
            plan = repo.crear_plan(dominio.nombre, dominio.id_nivel, dominio.lies_ids,
                                   ruta_membrete=dto.ruta_membrete)
            semestres_creados: dict[int, int] = {}

            for fila in dominio.filas:
                num = fila.numero_semestre

                # Crear semestre si no existe aún (incluye semestre 0 para optativas)
                if num not in semestres_creados:
                    semestres_creados[num] = repo.crear_semestre(
                        num, plan.id_plan,
                    ).id_semestre

                if fila.id_tipo == 1:
                    # ── TRONCO ──
                    # Buscar o crear la materia de tronco
                    mat = session.query(MateriaTroncoModel).filter_by(
                        nombre=fila.nombre_materia,
                    ).first()
                    if mat is None:
                        mat = MateriaTroncoModel(nombre=fila.nombre_materia)
                        session.add(mat)
                        session.flush()

                    # Crear detalle + asignación para CADA LIES
                    for lies_id in dominio.lies_ids:
                        detalle = repo.crear_detalle(
                            fila.nombre_materia,
                            semestres_creados[num],
                            fila.id_tipo,
                            lies_id,
                        )
                        repo.crear_asignacion_tronco(
                            detalle.id_detalle, mat.id_materia,
                        )
                else:
                    # ── OPTATIVA (semestre 0) ──
                    opt = OptativaModel(
                        nombre=fila.nombre_materia, id_plan=plan.id_plan,
                    )
                    session.add(opt)
                    session.flush()

                    # Crear detalle + asignación para CADA LIES
                    for lies_id in dominio.lies_ids:
                        detalle = repo.crear_detalle(
                            fila.nombre_materia,
                            semestres_creados[num],
                            fila.id_tipo,
                            lies_id,
                        )
                        repo.crear_asignacion_optativa(
                            detalle.id_detalle, opt.id_optativa,
                        )

            repo.commit()
            return True, f"Plan '{dominio.nombre}' creado correctamente."
        except Exception as exc:
            repo.rollback()
            return False, f"Error al guardar: {exc}"
        finally:
            session.close()