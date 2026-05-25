"""
Módulo de compatibilidad — Fase 14 completada.

HorarioStateManager es un alias de DetallePlanState.
La implementación real vive en:
    application/state/detalle_plan_state.py

Cualquier import existente de `HorarioStateManager` sigue funcionando.
"""
from application.state.detalle_plan_state import DetallePlanState as HorarioStateManager  # noqa: F401

__all__ = ["HorarioStateManager"]

