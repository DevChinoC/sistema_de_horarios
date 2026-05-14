"""Script de limpieza: consolida plan_generado duplicados.

Después de consolidar periodos duplicados, puede haber múltiples
plan_generado apuntando al mismo (id_plan, id_periodo).

Para cada grupo duplicado:
1. Conserva el plan_generado con ID más bajo (canónico)
2. Reasigna todos los horarios de los duplicados al canónico
3. Elimina los plan_generado duplicados
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import func
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import PlanGeneradoModel, HorarioModel

db = DatabaseConnection()
session = db.get_session()

try:
    # 1. Encontrar plan_generado duplicados por (id_plan, id_periodo)
    dupes = (
        session.query(
            PlanGeneradoModel.id_plan,
            PlanGeneradoModel.id_periodo,
            func.count(PlanGeneradoModel.id_plan_generado),
        )
        .group_by(PlanGeneradoModel.id_plan, PlanGeneradoModel.id_periodo)
        .having(func.count(PlanGeneradoModel.id_plan_generado) > 1)
        .all()
    )

    if not dupes:
        print("No hay plan_generado duplicados. Todo limpio.")
    else:
        for id_plan, id_periodo, count in dupes:
            print(f"\nPlan {id_plan}, Periodo {id_periodo}: {count} registros")
            ids = [
                r.id_plan_generado for r in
                session.query(PlanGeneradoModel)
                .filter_by(id_plan=id_plan, id_periodo=id_periodo)
                .order_by(PlanGeneradoModel.id_plan_generado)
                .all()
            ]
            canonical = ids[0]
            duplicates = ids[1:]
            print(f"  Canónico: {canonical}, Duplicados: {duplicates}")

            for dup_id in duplicates:
                affected = (
                    session.query(HorarioModel)
                    .filter(HorarioModel.id_plan_generado == dup_id)
                    .update({HorarioModel.id_plan_generado: canonical})
                )
                print(f"  Reasignados {affected} horarios de pg {dup_id} -> {canonical}")

                session.query(PlanGeneradoModel).filter(
                    PlanGeneradoModel.id_plan_generado == dup_id
                ).delete()
                print(f"  Eliminado plan_generado {dup_id}")

        session.commit()
        print("\n✅ Limpieza de plan_generado completada.")

except Exception as e:
    session.rollback()
    print(f"\n❌ Error: {e}")
finally:
    session.close()
