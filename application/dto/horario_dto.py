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


# ── Detalle completo de un horario (para edición) ────────────

@dataclass
class HorarioDetalleDTO:
    id_horario:      int
    id_asignacion:   int
    id_semestre:     int
    id_docente:      int
    id_aula:         int
    id_periodo:      int
    dia:             str
    hora_inicio:     str   # "HH:MM" 24h
    hora_fin:        str   # "HH:MM" 24h
    total_horas:     int
    periodo_nombre:  str


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
    id_lies:       int | None = None  # para separar plan_generado por LIES
    id_semestre:   int | None = None  # semestre seleccionado (real, no el de la asignación)


# ── Fila temporal de horario (formulario) ────────────────────

@dataclass
class FilaHorarioDTO:
    """Fila temporal de horario capturada del formulario."""
    dia: str
    hora_inicio: str  # "HH:MM" 24h
    hora_fin: str     # "HH:MM" 24h
    delta: int = 0    # horas calculadas

