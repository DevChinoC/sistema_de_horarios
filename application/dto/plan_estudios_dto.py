from dataclasses import dataclass, field


@dataclass
class FilaMateriaDTO:
    nombre_materia:  str
    id_tipo:         int
    numero_semestre: int


@dataclass
class CrearPlanDTO:
    nombre:   str
    id_nivel: int
    lies_ids: list[int]
    filas:    list[FilaMateriaDTO] = field(default_factory=list)
    ruta_membrete: str | None = None