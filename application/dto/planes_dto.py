from dataclasses import dataclass


@dataclass(frozen=True)
class NivelDTO:
    id: int
    nombre: str


@dataclass(frozen=True)
class PlanDTO:
    id: int
    nombre: str
    id_nivel: int
