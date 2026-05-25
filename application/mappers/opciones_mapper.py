"""
Mapper de opciones de Dropdown.

Convierte listas de DTOs de catálogo a opciones de Flet Dropdown.

NOTA: Este mapper SÍ importa Flet porque es de la capa UI.
Pero solo construye opciones — no lógica de negocio.
"""
from __future__ import annotations

import flet as ft

_NEGRO = "#000000"
_KEY_NUEVO = "__nuevo__"

# Fuente importada de plan_components para no hardcodear
try:
    from ui.components.plan_components import Fuentes, Colores
    _FUENTE = Fuentes.CAMPOS
    _COLOR_NUEVO = Colores.AZUL_PRIMARIO
except ImportError:
    _FUENTE = None
    _COLOR_NUEVO = "#1565C0"


def _text_style() -> ft.TextStyle:
    return ft.TextStyle(color=_NEGRO, font_family=_FUENTE)


class OpcionesMapper:
    """Convierte listas de DTOs a opciones de Dropdown de Flet."""

    # ── Catálogos ─────────────────────────────────────────────

    @staticmethod
    def docentes_a_opts(
        docentes: list,
        con_nuevo: bool = True,
    ) -> list[ft.dropdown.Option]:
        """Convierte lista de DocenteDTO a opciones de Dropdown.

        Args:
            docentes: Lista de DocenteDTO (id, nombre).
            con_nuevo: Si True agrega opción '+ Otro' al final.
        """
        opts = [
            ft.dropdown.Option(
                key=str(d.id),
                text=d.nombre,
                text_style=_text_style(),
            )
            for d in docentes
        ]
        if con_nuevo:
            opts.append(OpcionesMapper._opcion_nuevo())
        return opts

    @staticmethod
    def aulas_a_opts(
        aulas: list,
        con_nuevo: bool = True,
    ) -> list[ft.dropdown.Option]:
        """Convierte lista de AulaDTO a opciones de Dropdown."""
        opts = [
            ft.dropdown.Option(
                key=str(a.id),
                text=a.nombre,
                text_style=_text_style(),
            )
            for a in aulas
        ]
        if con_nuevo:
            opts.append(OpcionesMapper._opcion_nuevo())
        return opts

    @staticmethod
    def semestres_a_opts(semestres: list) -> list[ft.dropdown.Option]:
        """Convierte lista de SemestreDTO a opciones de Dropdown.

        Solo incluye semestres con numero > 0 (excluye optativas=0).
        """
        return [
            ft.dropdown.Option(
                key=str(s.id),
                text=f"Semestre {s.numero}",
                text_style=_text_style(),
            )
            for s in semestres
            if s.numero > 0
        ]

    @staticmethod
    def lies_a_opts(lies: list) -> list[ft.dropdown.Option]:
        """Convierte lista de LiesDTO a opciones de Dropdown."""
        return [
            ft.dropdown.Option(
                key=str(l.id),
                text=l.nombre,
                text_style=_text_style(),
            )
            for l in lies
        ]

    @staticmethod
    def dias_semana() -> list[ft.dropdown.Option]:
        """Opciones fijas de días de la semana."""
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        return [
            ft.dropdown.Option(key=d, text=d, text_style=_text_style())
            for d in dias
        ]

    # ── Helper privado ────────────────────────────────────────

    @staticmethod
    def _opcion_nuevo() -> ft.dropdown.Option:
        """Opción especial '+ Otro' para crear nuevos registros."""
        return ft.dropdown.Option(
            key=_KEY_NUEVO,
            content=ft.Container(
                content=ft.Text(
                    "+ Otro",
                    color="white",
                    size=13,
                    weight=ft.FontWeight.W_600,
                    font_family=_FUENTE,
                ),
                bgcolor=_COLOR_NUEVO,
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                expand=True,
            ),
        )
