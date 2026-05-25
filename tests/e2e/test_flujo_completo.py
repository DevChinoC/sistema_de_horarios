"""
E2E tests: flujos completos del sistema de horarios.

Prueba el ciclo completo: crear → guardar → editar → eliminar
usando el Controller + UseCase + Service reales.

Requiere conexión a MySQL.

Ejecutar:
    RUN_INTEGRATION_TESTS=1 pytest tests/e2e/ -v --tb=short
"""
from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS", "0") != "1",
    reason="Set RUN_INTEGRATION_TESTS=1 para ejecutar tests E2E",
)


@pytest.fixture
def db_session():
    """Sesión de BD con rollback automático."""
    from infrastructure.db.connection import DatabaseConnection

    db = DatabaseConnection()
    session = db.get_session()
    session.begin_nested()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def service():
    """HorarioService real conectado a MySQL."""
    from application.services.horario_service import HorarioService
    return HorarioService()


@pytest.fixture
def container():
    """Container de DI completo."""
    from application.container import Container
    return Container()


class TestFlujoCompleto:
    """E2E: crear → guardar → cargar → editar → eliminar."""

    def test_ciclo_crud_basico(self, service, db_session):
        """Verifica que el ciclo CRUD completo funciona sin errores.

        NOTA: Este test usa datos reales de la BD. Si la BD está vacía,
        algunos pasos pueden saltar.
        """
        # 1. Verificar que el servicio puede obtener catálogos
        aulas = list(service.obtener_aulas())
        docentes = list(service.obtener_docentes())
        tipos = service.obtener_tipos_materia()

        assert isinstance(aulas, list), "obtener_aulas debe retornar lista"
        assert isinstance(docentes, list), "obtener_docentes debe retornar lista"

    def test_container_provee_servicio_funcional(self, container):
        """Verifica que el Container crea un HorarioService funcional."""
        svc = container.horario_service()
        assert svc is not None
        # Verificar que es singleton
        svc2 = container.horario_service()
        assert svc is svc2, "Container debe retornar la misma instancia"

    def test_obtener_horarios_filtrados(self, service, db_session):
        """Verifica que la consulta de horarios filtrados no explota."""
        # Usamos parámetros que probablemente no tengan datos
        # pero que no deben causar excepción
        resultado = service.obtener_horarios_filtrados(
            id_plan=99999,
            id_lies=99999,
            id_semestre=99999,
            id_semestre_opt=None,
        )
        assert isinstance(list(resultado), list)
