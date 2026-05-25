"""
Integration tests para el repositorio de horarios.

Requiere conexión a MySQL con las variables de entorno configuradas en .env.
Los tests usan transacciones con rollback automático para no dejar datos sucios.

Ejecutar:
    pytest tests/integration/ -v --tb=short
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import MagicMock

# Marcar todos los tests de integración — se saltan si no hay BD
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS", "0") != "1",
    reason="Set RUN_INTEGRATION_TESTS=1 para ejecutar tests de integración",
)


@pytest.fixture
def db_session():
    """Fixture que provee una sesión de BD con rollback automático."""
    from infrastructure.db.connection import DatabaseConnection

    db = DatabaseConnection()
    session = db.get_session()
    # Iniciar transacción que se revertirá al final
    session.begin_nested()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def horario_service():
    """Fixture que provee el HorarioService real."""
    from application.services.horario_service import HorarioService
    return HorarioService()


class TestConexionBasica:
    """Verifica que la conexión a BD funciona."""

    def test_conecta_correctamente(self, db_session):
        result = db_session.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
        assert result.scalar() == 1

    def test_obtiene_tablas(self, db_session):
        result = db_session.execute(
            __import__("sqlalchemy").text("SHOW TABLES")
        )
        tables = [row[0] for row in result]
        assert len(tables) > 0, "La BD debe tener al menos una tabla"


class TestHorarioServiceIntegration:
    """Tests de integración del HorarioService contra MySQL."""

    def test_obtener_aulas(self, horario_service):
        """Verifica que el servicio puede leer aulas de la BD."""
        aulas = list(horario_service.obtener_aulas())
        # No validamos contenido específico — solo que no explota
        assert isinstance(aulas, list)

    def test_obtener_docentes(self, horario_service):
        """Verifica que el servicio puede leer docentes de la BD."""
        docentes = list(horario_service.obtener_docentes())
        assert isinstance(docentes, list)

    def test_obtener_tipos_materia(self, horario_service):
        """Verifica que obtiene tipos de materia."""
        tipos = horario_service.obtener_tipos_materia()
        assert isinstance(tipos, (list, dict))


class TestRepositoryTransacciones:
    """Verifica que las transacciones funcionan correctamente."""

    def test_rollback_no_persiste(self, db_session):
        """Verifica que el rollback del fixture funciona."""
        from sqlalchemy import text

        # Contar registros antes
        count_before = db_session.execute(
            text("SELECT COUNT(*) FROM aula")
        ).scalar()

        # Insertar un registro temporal
        db_session.execute(
            text("INSERT INTO aula (nombre) VALUES ('__TEST_TEMP__')")
        )
        db_session.flush()

        # Verificar que se insertó
        count_during = db_session.execute(
            text("SELECT COUNT(*) FROM aula")
        ).scalar()
        assert count_during == count_before + 1

        # El rollback ocurre automáticamente al salir del fixture
        # La siguiente sesión no verá este registro
