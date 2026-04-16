from dataclasses import dataclass


@dataclass
class HorarioDocenteFilaDTO:
    """Representa una entrada del horario semanal de un docente."""
    dia: str               # "Lunes", "Martes", …
    hora_inicio: str       # "HH:MM" 24h
    hora_fin: str          # "HH:MM" 24h
    nombre_materia: str
    nombre_lies: str = ""  # nombre de la LIES (útil para MIIDT)


@dataclass
class HorarioDocenteResumenDTO:
    """Datos de contexto para el encabezado del documento Word."""
    nombre_docente: str
    nombre_plan: str
    semestre: int
    filas: list  # list[HorarioDocenteFilaDTO]
