"""Tests unitarios para CrearHorarioUseCase con mocks."""
from unittest.mock import MagicMock, patch
import pytest

from application.use_cases.crear_horario import CrearHorarioUseCase
from application.dto.horario_dto import GuardarHorarioDTO
from domain.exceptions.horario_exceptions import (
    HorarioConflictException,
    HorarioInvalidoException,
)
from domain.rules.horario_validator import HorarioValidator


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_dto(**kwargs):
    defaults = dict(
        id_asignacion=1,
        id_docente=1,
        id_aula=1,
        id_periodo=1,
        dia="Lunes",
        hora_inicio="07:00",
        hora_fin="09:00",
        total_horas=2,
        id_plan=1,
        id_lies=1,
        id_semestre=1,
    )
    defaults.update(kwargs)
    return GuardarHorarioDTO(**defaults)


@pytest.fixture
def repo():
    """Mock de IHorarioRepository."""
    mock = MagicMock()
    mock.obtener_id_materia.return_value = None          # optativa por defecto
    mock.obtener_o_crear_plan_generado.return_value = MagicMock(id_plan_generado=10)
    mock.crear.return_value = 42                         # id_horario retornado
    mock.commit.return_value = None
    return mock


@pytest.fixture
def uc(repo):
    return CrearHorarioUseCase(repo=repo, validator=HorarioValidator())


# ── Casos felices ─────────────────────────────────────────────────────────────

class TestCrearHorarioUCOk:
    def test_retorna_id_horario(self, uc, repo):
        dto = make_dto()
        id_h = uc.ejecutar(dto)
        assert id_h == 42

    def test_llama_crear_en_repo(self, uc, repo):
        dto = make_dto()
        uc.ejecutar(dto)
        repo.crear.assert_called_once()

    def test_llama_commit(self, uc, repo):
        dto = make_dto()
        uc.ejecutar(dto)
        repo.commit.assert_called_once()

    def test_con_horarios_existentes_sin_conflicto(self, uc, repo):
        """Optativa nueva sin solapar existente."""
        from domain.entities.horario import Horario
        existente = Horario(
            dia="Lunes", hora_inicio="09:00", hora_fin="11:00",
            id_asignacion=2, id_docente=1, id_aula=1,
            id_periodo=1, id_semestre=1, id_lies=1,
            id_materia=None, id_horario=5,
        )
        dto = make_dto(hora_inicio="07:00", hora_fin="09:00")
        id_h = uc.ejecutar(dto, horarios_existentes=[existente])
        assert id_h == 42


# ── Casos de error ────────────────────────────────────────────────────────────

class TestCrearHorarioUCError:
    def test_lanza_si_inicio_igual_fin(self, uc, repo):
        dto = make_dto(hora_inicio="09:00", hora_fin="09:00")
        with pytest.raises(HorarioInvalidoException):
            uc.ejecutar(dto)
        repo.crear.assert_not_called()

    def test_lanza_si_inicio_mayor_fin(self, uc, repo):
        dto = make_dto(hora_inicio="10:00", hora_fin="08:00")
        with pytest.raises(HorarioInvalidoException):
            uc.ejecutar(dto)
        repo.crear.assert_not_called()

    def test_lanza_conflict_con_traslape(self, uc, repo):
        """Optativa nueva que solapa con existente."""
        from domain.entities.horario import Horario
        existente = Horario(
            dia="Lunes", hora_inicio="07:00", hora_fin="09:00",
            id_asignacion=2, id_docente=1, id_aula=1,
            id_periodo=1, id_semestre=1, id_lies=1,
            id_materia=None, id_horario=5,
        )
        dto = make_dto(hora_inicio="08:00", hora_fin="10:00")
        with pytest.raises(HorarioConflictException):
            uc.ejecutar(dto, horarios_existentes=[existente])
        repo.crear.assert_not_called()

    def test_no_llama_commit_si_falla(self, uc, repo):
        dto = make_dto(hora_inicio="09:00", hora_fin="09:00")
        with pytest.raises(HorarioInvalidoException):
            uc.ejecutar(dto)
        repo.commit.assert_not_called()
