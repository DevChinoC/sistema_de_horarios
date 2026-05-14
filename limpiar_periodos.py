"""Script de limpieza: consolida periodos duplicados (mismo nombre, diferente ID).

Para cada nombre de periodo con múltiples IDs:
1. Conserva el ID más bajo (el "canónico")
2. Actualiza plan_generado que referencian IDs duplicados al canónico
3. Elimina los registros de periodo duplicados

Ejecutar UNA vez. Hacer backup de la BD antes.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import PeriodoEscolarModel, PlanGeneradoModel

db = DatabaseConnection()
session = db.get_session()

try:
    # 1. Encontrar periodos duplicados
    from sqlalchemy import func
    dupes = (
        session.query(PeriodoEscolarModel.nombre, func.count(PeriodoEscolarModel.id_periodo))
        .group_by(PeriodoEscolarModel.nombre)
        .having(func.count(PeriodoEscolarModel.id_periodo) > 1)
        .all()
    )

    if not dupes:
        print("No hay periodos duplicados. Todo limpio.")
    else:
        for nombre, count in dupes:
            print(f"\nPeriodo '{nombre}': {count} registros duplicados")
            ids = [
                r.id_periodo for r in
                session.query(PeriodoEscolarModel)
                .filter(PeriodoEscolarModel.nombre == nombre)
                .order_by(PeriodoEscolarModel.id_periodo)
                .all()
            ]
            canonical = ids[0]
            duplicates = ids[1:]
            print(f"  Canónico: {canonical}, Duplicados: {duplicates}")

            # 2. Reasignar plan_generado
            for dup_id in duplicates:
                affected = (
                    session.query(PlanGeneradoModel)
                    .filter(PlanGeneradoModel.id_periodo == dup_id)
                    .update({PlanGeneradoModel.id_periodo: canonical})
                )
                print(f"  Reasignados {affected} plan_generado de periodo {dup_id} -> {canonical}")

            # 3. Eliminar duplicados
            for dup_id in duplicates:
                session.query(PeriodoEscolarModel).filter(
                    PeriodoEscolarModel.id_periodo == dup_id
                ).delete()
                print(f"  Eliminado periodo {dup_id}")

        session.commit()
        print("\n✅ Limpieza completada exitosamente.")

except Exception as e:
    session.rollback()
    print(f"\n❌ Error: {e}")
finally:
    session.close()
