"""Tests unitarios para la entidad Horario."""
import pytest
from domain.entities.horario import Horario
from domain.exceptions.horario_exceptions import HorarioInvalidoException


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_horario(**kwargs) -> Horario:
    """Crea un Horario con valores por defecto, sobreescribibles por kwargs."""
    defaults = dict(
        dia="Lunes",
        hora_inicio="07:00",
        hora_fin="09:00",
        id_asignacion=1,
        id_docente=1,
        id_aula=1,
        id_periodo=1,
        id_semestre=1,
        id_lies=1,
        id_materia=None,
    )
    defaults.update(kwargs)
    return Horario(**defaults)


# ── Construcción válida ────────────────────────────────────────────────────────

class TestHorarioCreacion:
    def test_crea_correctamente_con_strings(self):
        h = make_horario()
        assert str(h.dia) == "Lunes"
        assert str(h.hora_inicio) == "07:00"
        assert str(h.hora_fin) == "09:00"

    def test_crea_correctamente_con_value_objects(self):
        from domain.value_objects.hora import Hora
        from domain.value_objects.dia_semana import DiaSemana
        h = make_horario(dia=DiaSemana("Martes"), hora_inicio=Hora("08:00"), hora_fin=Hora("10:00"))
        assert str(h.dia) == "Martes"

    def test_lanza_si_inicio_igual_a_fin(self):
        with pytest.raises(HorarioInvalidoException) as exc_info:
            make_horario(hora_inicio="09:00", hora_fin="09:00")
        assert "anterior" in str(exc_info.value)

    def test_lanza_si_inicio_mayor_que_fin(self):
        with pytest.raises(HorarioInvalidoException):
            make_horario(hora_inicio="10:00", hora_fin="08:00")


# ── calcular_duracion ─────────────────────────────────────────────────────────

class TestCalcularDuracion:
    def test_dos_horas(self):
        h = make_horario(hora_inicio="07:00", hora_fin="09:00")
        assert h.calcular_duracion() == pytest.approx(2.0)

    def test_hora_y_media(self):
        h = make_horario(hora_inicio="08:00", hora_fin="09:30")
        assert h.calcular_duracion() == pytest.approx(1.5)

    def test_duracion_entera(self):
        h = make_horario(hora_inicio="07:00", hora_fin="10:00")
        assert h.calcular_duracion_enteros() == 3


# ── traslapa ──────────────────────────────────────────────────────────────────

class TestTraslapa:
    def test_sin_traslape_dias_distintos(self):
        h1 = make_horario(dia="Lunes",   hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Martes",  hora_inicio="07:00", hora_fin="09:00")
        assert not h1.traslapa(h2)

    def test_sin_traslape_consecutivos(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Lunes", hora_inicio="09:00", hora_fin="11:00")
        assert not h1.traslapa(h2)

    def test_con_traslape_parcial(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Lunes", hora_inicio="08:00", hora_fin="10:00")
        assert h1.traslapa(h2)
        assert h2.traslapa(h1)

    def test_con_traslape_completo_contenido(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="11:00")
        h2 = make_horario(dia="Lunes", hora_inicio="08:00", hora_fin="10:00")
        assert h1.traslapa(h2)

    def test_identico(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        assert h1.traslapa(h2)


# ── es_tronco_comun ───────────────────────────────────────────────────────────

class TestEsTroncoComun:
    def test_es_tronco_si_tiene_id_materia(self):
        h = make_horario(id_materia=5)
        assert h.es_tronco_comun() is True

    def test_no_es_tronco_si_id_materia_none(self):
        h = make_horario(id_materia=None)
        assert h.es_tronco_comun() is False


# ── mismo_rango_que ───────────────────────────────────────────────────────────

class TestMismoRangoQue:
    def test_mismo_rango(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        assert h1.mismo_rango_que(h2)

    def test_diferente_hora(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="10:00")
        assert not h1.mismo_rango_que(h2)

    def test_diferente_dia(self):
        h1 = make_horario(dia="Lunes", hora_inicio="07:00", hora_fin="09:00")
        h2 = make_horario(dia="Martes", hora_inicio="07:00", hora_fin="09:00")
        assert not h1.mismo_rango_que(h2)
