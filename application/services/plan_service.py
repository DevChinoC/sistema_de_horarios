class PlanService:
    def __init__(self, repository):
        self.repository = repository

    def crear_plan_completo(self, nombre: str, id_nivel: int, ids_lies: list[int]):
        if not nombre.strip():
            raise ValueError("El nombre del plan es obligatorio")

        plan = self.repository.crear_plan(nombre, id_nivel)

        if ids_lies:
            self.repository.vincular_lies(plan.id_plan, ids_lies)

        return plan