from dataclasses import dataclass, field


@dataclass
class FilaMateria:
    nombre_materia:  str
    id_tipo:         int
    numero_semestre: int


@dataclass
class PlanEstudiosDomain:
    nombre:   str
    id_nivel: int
    lies_ids: list[int]
    filas:    list[FilaMateria] = field(default_factory=list)

    def agregar_fila(self, fila: FilaMateria) -> None:
        self.filas.append(fila)

    def es_valido(self) -> tuple[bool, str]:
        if not self.nombre.strip():
            return False, "El nombre del plan no puede estar vacío."
        if not self.lies_ids:
            return False, "Selecciona al menos una LIES."
        if not self.filas:
            return False, "Agrega al menos una materia al plan."
        for i, f in enumerate(self.filas):
            if not f.nombre_materia.strip():
                return False, f"La fila {i+1} no tiene nombre de materia."
            # Semestre 0 = Optativa (válido). Tronco requiere 1-8.
            es_optativa = (f.id_tipo == 2)
            if es_optativa and f.numero_semestre != 0:
                return False, f"La fila {i+1}: optativa debe tener semestre 0."
            if not es_optativa and f.numero_semestre < 1:
                return False, f"La fila {i+1} tiene semestre inválido."
        return True, ""