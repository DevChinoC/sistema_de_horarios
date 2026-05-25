"""
Contenedor de Inyección de Dependencias (DI Container).

Centraliza la construcción y el ciclo de vida de todas las dependencias
del sistema. Elimina el acoplamiento rígido donde las clases instancian
sus propias dependencias con `new` / llamadas directas al constructor.

Uso:
    container = Container()
    controller = container.detalle_plan_controller(id_plan=1)

PROHIBIDO: lógica de negocio aquí.
PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations


class Container:
    """Contenedor simple de dependencias (sin framework externo).

    Implementa un Service Locator minimalista. Cada método factory
    retorna una nueva instancia por defecto (prototype scope).
    Para instancias compartidas usa los métodos con prefijo `shared_`.
    """

    def __init__(self) -> None:
        # Instancias compartidas (singletons de sesión)
        self._horario_service = None

    # ── Infraestructura ───────────────────────────────────────

    def horario_service(self):
        """Retorna la instancia compartida de HorarioService."""
        if self._horario_service is None:
            from application.services.horario_service import HorarioService
            self._horario_service = HorarioService()
        return self._horario_service

    # ── Domain ────────────────────────────────────────────────

    def horario_validator(self):
        """Nueva instancia de HorarioValidator (stateless, seguro compartir)."""
        from domain.rules.horario_validator import HorarioValidator
        return HorarioValidator()

    def docente_validator(self):
        from domain.rules.docente_validator import DocenteValidator
        return DocenteValidator()

    def salon_validator(self):
        from domain.rules.salon_validator import SalonValidator
        return SalonValidator()

    # ── Use Cases ─────────────────────────────────────────────

    def crear_horario_use_case(self):
        """Nueva instancia de CrearHorarioUseCase."""
        from application.use_cases.crear_horario import CrearHorarioUseCase
        # Nota: los use cases usan IHorarioRepository; por ahora usamos
        # HorarioService como proxy hasta que se complete la migración de Fase 7.
        return CrearHorarioUseCase(
            repo=self._make_repo_adapter(),
            validator=self.horario_validator(),
        )

    def editar_horario_use_case(self):
        from application.use_cases.editar_horario import EditarHorarioUseCase
        return EditarHorarioUseCase(
            repo=self._make_repo_adapter(),
            validator=self.horario_validator(),
        )

    def eliminar_horario_use_case(self):
        from application.use_cases.eliminar_horario import EliminarHorarioUseCase
        return EliminarHorarioUseCase(repo=self._make_repo_adapter())

    def guardar_plan_use_case(self):
        from application.use_cases.guardar_plan import GuardarPlanUseCase
        return GuardarPlanUseCase(
            repo=self._make_repo_adapter(),
            validator=self.horario_validator(),
        )

    # ── Application State ─────────────────────────────────────

    def detalle_plan_state(
        self,
        id_plan: int,
        id_lies_activa: int,
        sem_opt_id: int | None = None,
    ):
        """Nueva instancia de DetallePlanState para una sesión de pantalla."""
        from application.state.detalle_plan_state import DetallePlanState
        return DetallePlanState(
            service=self.horario_service(),
            id_plan=id_plan,
            id_lies_activa=id_lies_activa,
            sem_opt_id=sem_opt_id,
        )

    # ── Controllers ───────────────────────────────────────────

    def detalle_plan_controller(
        self,
        id_plan: int,
        id_lies_activa: int,
        sem_opt_id: int | None = None,
    ):
        """Nueva instancia de DetallePlanController lista para usar.

        Ejemplo:
            ctrl = container.detalle_plan_controller(id_plan=1)
        """
        from application.controllers.detalle_plan_controller import DetallePlanController
        state = self.detalle_plan_state(id_plan, id_lies_activa, sem_opt_id)
        return DetallePlanController(
            service=self.horario_service(),
            state=state,
            id_plan=id_plan,
        )

    # ── Helpers privados ──────────────────────────────────────

    def _make_repo_adapter(self):
        """Adaptador temporal que envuelve HorarioService como IHorarioRepository.

        Permite que los use cases funcionen con la interfaz IHorarioRepository
        sin necesidad de reescribir el repositorio MySQL aún.

        TODO (Fase 7 completa): reemplazar por MySQLHorarioRepository
        cuando implemente IHorarioRepository directamente.
        """
        return _HorarioServiceRepoAdapter(self.horario_service())


class _HorarioServiceRepoAdapter:
    """Adaptador que permite usar HorarioService como IHorarioRepository.

    Implementa el subconjunto de IHorarioRepository necesario para
    los use cases sin tocar el repositorio MySQL existente.

    Se elimina en Fase 7 (completa) cuando HorarioRepository
    implemente IHorarioRepository directamente.
    """

    def __init__(self, service) -> None:
        self._svc = service

    def obtener_id_materia(self, id_asignacion: int):
        return self._svc.obtener_id_materia(id_asignacion)

    def obtener_o_crear_plan_generado(self, id_plan, id_periodo, id_lies):
        # Acceso directo al repo interno del service para el plan_generado
        from infrastructure.db.connection import DatabaseConnection
        from infrastructure.repositories.horario_repository import HorarioRepository
        db = DatabaseConnection()
        session = db.get_session()
        try:
            repo = HorarioRepository(session)
            return repo.obtener_o_crear_plan_generado(id_plan, id_periodo, id_lies)
        finally:
            session.close()

    def crear(self, id_plan_generado, id_asignacion, id_docente,
              id_aula, dia, hora_inicio, hora_fin, total_horas, id_semestre):
        from infrastructure.db.connection import DatabaseConnection
        from infrastructure.repositories.horario_repository import HorarioRepository
        db = DatabaseConnection()
        session = db.get_session()
        try:
            repo = HorarioRepository(session)
            h = repo.crear_horario(
                id_plan_generado=id_plan_generado,
                id_asignacion=id_asignacion,
                id_docente=id_docente,
                id_aula=id_aula,
                dia=dia,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                total_horas=total_horas,
                id_semestre=id_semestre,
            )
            repo.commit()
            return h.id_horario
        except Exception:
            repo.rollback()
            raise
        finally:
            session.close()

    def actualizar(self, id_horario, id_asignacion, id_docente, id_aula,
                   id_periodo, dia, hora_inicio, hora_fin, total_horas, id_semestre):
        from infrastructure.db.connection import DatabaseConnection
        from infrastructure.repositories.horario_repository import HorarioRepository
        db = DatabaseConnection()
        session = db.get_session()
        try:
            repo = HorarioRepository(session)
            repo.actualizar_horario(
                id_horario=id_horario, id_asignacion=id_asignacion,
                id_docente=id_docente, id_aula=id_aula, id_periodo=id_periodo,
                dia=dia, hora_inicio=hora_inicio, hora_fin=hora_fin,
                total_horas=total_horas, id_semestre=id_semestre,
            )
            repo.commit()
        except Exception:
            repo.rollback()
            raise
        finally:
            session.close()

    def eliminar(self, id_horario: int) -> None:
        from infrastructure.db.connection import DatabaseConnection
        from infrastructure.repositories.horario_repository import HorarioRepository
        db = DatabaseConnection()
        session = db.get_session()
        try:
            repo = HorarioRepository(session)
            repo.eliminar_horario(id_horario)
            repo.commit()
        except Exception:
            repo.rollback()
            raise
        finally:
            session.close()

    def obtener_por_id(self, id_horario: int):
        return self._svc.obtener_horario_detalle(id_horario)

    def obtener_filtrados(self, id_plan, id_lies, id_semestre, id_semestre_opt=None):
        return self._svc.obtener_horarios_filtrados(
            id_plan, id_lies, id_semestre, id_semestre_opt)

    def obtener_de_plan_generado(self, id_plan_generado):
        return self._svc.obtener_horarios_de_plan_generado(id_plan_generado)

    def obtener_docentes(self):
        return self._svc.obtener_docentes()

    def crear_docente(self, nombre: str):
        return self._svc.crear_docente(nombre)

    def obtener_aulas(self):
        return self._svc.obtener_aulas()

    def crear_aula(self, nombre: str):
        return self._svc.crear_aula(nombre)

    def crear_periodo(self, nombre: str):
        return self._svc.crear_periodo(nombre)

    def obtener_semestres(self, id_plan: int):
        return self._svc.obtener_semestres(id_plan)

    def obtener_unidades(self, id_plan, id_lies, id_semestre):
        return self._svc.obtener_unidades(id_plan, id_lies, id_semestre)

    def eliminar_plan_generado(self, id_plan_generado: int) -> None:
        ok, msg = self._svc.eliminar_plan_generado(id_plan_generado)
        if not ok:
            raise RuntimeError(msg)

    def commit(self) -> None:
        pass  # ya se hace commit dentro de cada método

    def rollback(self) -> None:
        pass  # ya se hace rollback dentro de cada método
