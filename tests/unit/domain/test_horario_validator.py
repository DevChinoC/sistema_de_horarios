"""Tests unitarios para HorarioValidator (reglas de negocio)."""
import pytest
from domain.entities.horario import Horario
from domain.exceptions.horario_exceptions import HorarioConflictException
from domain.rules.horario_validator import HorarioValidator


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def validator():
    return HorarioValidator()


def h(dia="Lunes", inicio="07:00", fin="09:00", id_materia=None,
      id_lies=1, id_aula=1, id_docente=1, id_horario=None):
    """Fábrica compacta de Horario para tests."""
    return Horario(
        dia=dia, hora_inicio=inicio, hora_fin=fin,
        id_asignacion=1, id_docente=id_docente, id_aula=id_aula,
        id_periodo=1, id_semestre=1, id_lies=id_lies,
        id_materia=id_materia, id_horario=id_horario,
    )


# ── Regla 1: tronco en otra LIES debe ser idéntico ────────────────────────────

class TestRegla1TroncoConsistente:
    def test_tronco_misma_lies_sin_conflicto(self, validator):
        """Tronco de la misma LIES no se valida con Regla 1."""
        nuevo = h(id_materia=10, id_lies=1)
        existentes = [h(id_materia=10, id_lies=1)]
        # No debe lanzar — misma LIES
        validator.validar_traslapes(nuevo, existentes)

    def test_tronco_otra_lies_mismo_horario_ok(self, validator):
        """Mismo día/hora/aula/docente en otra LIES → OK."""
        nuevo = h(dia="Lunes", inicio="07:00", fin="09:00",
                  id_materia=10, id_lies=2, id_aula=5, id_docente=3)
        existentes = [h(dia="Lunes", inicio="07:00", fin="09:00",
                        id_materia=10, id_lies=1, id_aula=5, id_docente=3)]
        validator.validar_traslapes(nuevo, existentes)  # no lanza

    def test_tronco_otra_lies_diferente_horario_falla(self, validator):
        """Diferente horario en otra LIES → HorarioConflictException."""
        nuevo = h(dia="Lunes", inicio="07:00", fin="09:00",
                  id_materia=10, id_lies=2)
        existentes = [h(dia="Martes", inicio="07:00", fin="09:00",
                        id_materia=10, id_lies=1)]
        with pytest.raises(HorarioConflictException):
            validator.validar_traslapes(nuevo, existentes)

    def test_tronco_otra_lies_diferente_aula_falla(self, validator):
        """Mismo horario pero diferente aula en otra LIES → falla."""
        nuevo = h(dia="Lunes", inicio="07:00", fin="09:00",
                  id_materia=10, id_lies=2, id_aula=99)
        existentes = [h(dia="Lunes", inicio="07:00", fin="09:00",
                        id_materia=10, id_lies=1, id_aula=1)]
        with pytest.raises(HorarioConflictException):
            validator.validar_traslapes(nuevo, existentes)

    def test_tronco_otra_lies_diferente_docente_falla(self, validator):
        """Mismo horario pero diferente docente en otra LIES → falla."""
        nuevo = h(dia="Lunes", inicio="07:00", fin="09:00",
                  id_materia=10, id_lies=2, id_docente=99)
        existentes = [h(dia="Lunes", inicio="07:00", fin="09:00",
                        id_materia=10, id_lies=1, id_docente=1)]
        with pytest.raises(HorarioConflictException):
            validator.validar_traslapes(nuevo, existentes)


# ── Regla 2: dos troncos distintos no se solapan ──────────────────────────────

class TestRegla2TroncoVsTronco:
    def test_dos_troncos_sin_traslape_ok(self, validator):
        nuevo = h(dia="Lunes", inicio="09:00", fin="11:00", id_materia=10)
        existentes = [h(dia="Lunes", inicio="07:00", fin="09:00", id_materia=20)]
        validator.validar_traslapes(nuevo, existentes)  # no lanza

    def test_dos_troncos_con_traslape_falla(self, validator):
        nuevo = h(dia="Lunes", inicio="08:00", fin="10:00", id_materia=10)
        existentes = [h(dia="Lunes", inicio="07:00", fin="09:00", id_materia=20)]
        with pytest.raises(HorarioConflictException):
            validator.validar_traslapes(nuevo, existentes)

    def test_dos_troncos_dias_distintos_ok(self, validator):
        nuevo = h(dia="Martes", inicio="07:00", fin="09:00", id_materia=10)
        existentes = [h(dia="Lunes", inicio="07:00", fin="09:00", id_materia=20)]
        validator.validar_traslapes(nuevo, existentes)  # no lanza


# ── Regla 3: optativa vs tronco ───────────────────────────────────────────────

class TestRegla3OptativaVsTronco:
    def test_optativa_sin_traslape_con_tronco_ok(self, validator):
        optativa = h(dia="Lunes", inicio="09:00", fin="11:00", id_materia=None)
        tronco   = h(dia="Lunes", inicio="07:00", fin="09:00", id_materia=10)
        validator.validar_traslapes(optativa, [tronco])  # no lanza

    def test_optativa_con_traslape_sobre_tronco_falla(self, validator):
        optativa = h(dia="Lunes", inicio="08:00", fin="10:00", id_materia=None)
        tronco   = h(dia="Lunes", inicio="07:00", fin="09:00", id_materia=10)
        with pytest.raises(HorarioConflictException):
            validator.validar_traslapes(optativa, [tronco])


# ── Regla 4: optativa vs optativa en la misma LIES ────────────────────────────

class TestRegla4OptativaVsOptativa:
    def test_dos_optativas_sin_traslape_ok(self, validator):
        nueva = h(dia="Lunes", inicio="09:00", fin="11:00",
                  id_materia=None, id_lies=1, id_horario=None)
        existente = h(dia="Lunes", inicio="07:00", fin="09:00",
                      id_materia=None, id_lies=1, id_horario=5)
        validator.validar_traslapes(nueva, [existente])  # no lanza

    def test_dos_optativas_con_traslape_falla(self, validator):
        nueva = h(dia="Lunes", inicio="08:00", fin="10:00",
                  id_materia=None, id_lies=1)
        existente = h(dia="Lunes", inicio="07:00", fin="09:00",
                      id_materia=None, id_lies=1, id_horario=5)
        with pytest.raises(HorarioConflictException):
            validator.validar_traslapes(nueva, [existente])

    def test_optativas_en_lies_distintas_ok(self, validator):
        """Optativas en LIES distintas no se validan entre sí."""
        nueva = h(dia="Lunes", inicio="08:00", fin="10:00",
                  id_materia=None, id_lies=2)
        existente = h(dia="Lunes", inicio="07:00", fin="09:00",
                      id_materia=None, id_lies=1, id_horario=5)
        validator.validar_traslapes(nueva, [existente])  # no lanza

    def test_excluye_horario_editado(self, validator):
        """Al editar, el propio horario no genera conflicto consigo mismo."""
        editado = h(dia="Lunes", inicio="07:00", fin="09:00",
                    id_materia=None, id_lies=1, id_horario=99)
        validator.validar_traslapes(editado, [editado], id_horario_excluir=99)
