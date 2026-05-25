"""Tests unitarios para los Value Objects del dominio."""
import pytest
from domain.value_objects.hora import Hora
from domain.value_objects.dia_semana import DiaSemana
from domain.value_objects.periodo import Periodo
from domain.value_objects.salon import Salon
from domain.value_objects.grupo import Grupo


# ── Hora ──────────────────────────────────────────────────────────────────────

class TestHora:
    def test_crea_hora_valida(self):
        h = Hora("07:30")
        assert h.valor == "07:30"

    def test_crea_medianoche(self):
        h = Hora("00:00")
        assert h.valor == "00:00"

    def test_crea_ultima_hora(self):
        h = Hora("23:59")
        assert h.valor == "23:59"

    def test_lanza_hora_invalida_formato(self):
        # Formato sin dos partes no es válido
        with pytest.raises(ValueError):
            Hora("0730")    # sin ":"
        with pytest.raises(ValueError):
            Hora("25:00")   # hora fuera de rango

    def test_lanza_hora_invalida_caracteres(self):
        with pytest.raises(ValueError):
            Hora("aa:bb")

    def test_lanza_minutos_invalidos(self):
        with pytest.raises(ValueError):
            Hora("07:60")

    def test_comparacion_menor(self):
        assert Hora("07:00") < Hora("09:00")

    def test_comparacion_mayor(self):
        assert Hora("10:00") > Hora("08:00")

    def test_comparacion_igual(self):
        assert Hora("07:00") == Hora("07:00")

    def test_en_minutos(self):
        h = Hora("08:30")
        assert h.en_minutos() == 8 * 60 + 30

    def test_to_time(self):
        from datetime import time
        h = Hora("07:00")
        assert h.to_time() == time(7, 0)

    def test_str(self):
        h = Hora("09:00")
        assert str(h) == "09:00"

    def test_hash_iguales(self):
        assert hash(Hora("07:00")) == hash(Hora("07:00"))


# ── DiaSemana ─────────────────────────────────────────────────────────────────

class TestDiaSemana:
    @pytest.mark.parametrize("valor,esperado", [
        ("Lunes", "Lunes"),
        ("lunes", "Lunes"),
        ("LUNES", "Lunes"),
        ("Miércoles", "Miércoles"),
        ("miercoles", "Miércoles"),
        ("Sábado", "Sábado"),
        ("sabado", "Sábado"),
        ("Domingo", "Domingo"),
    ])
    def test_normaliza_correctamente(self, valor, esperado):
        d = DiaSemana(valor)
        assert d.valor == esperado

    def test_lanza_dia_invalido(self):
        with pytest.raises(ValueError):
            DiaSemana("Marte")

    def test_lanza_cadena_vacia(self):
        with pytest.raises(ValueError):
            DiaSemana("")

    def test_indice_lunes_es_cero(self):
        assert DiaSemana("Lunes").indice == 0

    def test_indice_domingo_es_seis(self):
        assert DiaSemana("Domingo").indice == 6

    def test_fin_de_semana(self):
        assert DiaSemana("Sábado").es_fin_de_semana() is True
        assert DiaSemana("Lunes").es_fin_de_semana() is False

    def test_comparacion_orden(self):
        assert DiaSemana("Lunes") < DiaSemana("Martes")
        assert DiaSemana("Viernes") > DiaSemana("Lunes")

    def test_igualdad_con_string(self):
        assert DiaSemana("Lunes") == "Lunes"

    def test_hash(self):
        assert hash(DiaSemana("Lunes")) == hash(DiaSemana("Lunes"))


# ── Periodo ───────────────────────────────────────────────────────────────────

class TestPeriodo:
    def test_crea_periodo_valido(self):
        p = Periodo("Feb-Jun 2024")
        assert p.nombre == "Feb-Jun 2024"

    def test_elimina_espacios_extremos(self):
        p = Periodo("  Ago-Dic 2025  ")
        assert p.nombre == "Ago-Dic 2025"

    def test_lanza_si_vacio(self):
        with pytest.raises(ValueError):
            Periodo("")

    def test_lanza_si_solo_espacios(self):
        with pytest.raises(ValueError):
            Periodo("   ")

    def test_lanza_si_demasiado_largo(self):
        with pytest.raises(ValueError):
            Periodo("A" * 101)

    def test_igualdad(self):
        assert Periodo("Feb-Jun 2024") == Periodo("Feb-Jun 2024")

    def test_igualdad_con_string(self):
        assert Periodo("Feb-Jun 2024") == "Feb-Jun 2024"


# ── Salon ─────────────────────────────────────────────────────────────────────

class TestSalon:
    def test_crea_salon_valido(self):
        s = Salon("A-101")
        assert s.nombre == "A-101"

    def test_lanza_si_vacio(self):
        with pytest.raises(ValueError):
            Salon("")

    def test_igualdad_case_insensitive(self):
        assert Salon("A-101") == Salon("a-101")

    def test_lanza_si_demasiado_largo(self):
        with pytest.raises(ValueError):
            Salon("X" * 101)


# ── Grupo ─────────────────────────────────────────────────────────────────────

class TestGrupo:
    def test_crea_grupo_valido(self):
        g = Grupo("A")
        assert g.identificador == "A"

    def test_lanza_si_vacio(self):
        with pytest.raises(ValueError):
            Grupo("")

    def test_igualdad(self):
        assert Grupo("A") == Grupo("A")

    def test_no_igualdad(self):
        assert Grupo("A") != Grupo("B")
