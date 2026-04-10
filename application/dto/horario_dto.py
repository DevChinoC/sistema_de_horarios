from dataclasses import dataclass, field


# ── Catálogos ────────────────────────────────────────────────

@dataclass(frozen=True)
class LiesDTO:
    id: int
    nombre: str


@dataclass(frozen=True)
class SemestreDTO:
    id: int
    numero: int


@dataclass(frozen=True)
class UnidadAprendizajeDTO:
    """Representa una materia (tronco u optativa) con su detalle."""
    id_detalle: int
    id_asignacion: int
    nombre: str
    tipo: str           # "Tronco" | "Optativa"
    numero_semestre: int
    id_lies: int


@dataclass(frozen=True)
class DocenteDTO:
    id: int
    nombre: str


@dataclass(frozen=True)
class AulaDTO:
    id: int
    nombre: str


@dataclass(frozen=True)
class PeriodoDTO:
    id: int
    nombre: str


# ── Horario registrado ────────────────────────────────────────

@dataclass
class HorarioRegistradoDTO:
    id_horario:      int
    clave:           str   # número de orden (001, 002…)
    semestre:        str
    unidad:          str
    docente:         str
    aulas:           str
    periodo:         str
    total_horas:     int
    dia:             str = ""   # "Lunes", "Martes", …
    hora_inicio:     str = ""   # "HH:MM" 24h
    hora_fin:        str = ""   # "HH:MM" 24h
    numero_semestre: int = 0    # entero para tabla del PDF


# ── Comando para guardar un horario ──────────────────────────

@dataclass
class GuardarHorarioDTO:
    id_asignacion: int
    id_docente:    int
    id_aula:       int
    id_periodo:    int
    dia:           str
    hora_inicio:   str   # "HH:MM"
    hora_fin:      str   # "HH:MM"
    total_horas:   int
    id_plan:       int
