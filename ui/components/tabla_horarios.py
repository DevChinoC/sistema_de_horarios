"""
Componente UI: TablaHorarios

Tabla de horarios registrados con acciones de editar y eliminar.
Extraído de DetallePlanView para convertirlo en componente reutilizable.

SOLO UI: no contiene lógica de negocio.
"""
from __future__ import annotations

from functools import partial
from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes


class TablaHorarios(ft.DataTable):
    """DataTable de horarios registrados con botones Editar/Eliminar.

    Uso:
        tabla = TablaHorarios(
            on_editar=lambda id_h: ...,
            on_eliminar=lambda id_h: ...,
        )
        tabla.cargar(registros)
    """

    _COLUMNAS = [
        "Clave", "Semestre", "Unidad de aprendizaje",
        "Docente", "Horas", "Aula", "Periodo", "Acción",
    ]

    def __init__(
        self,
        on_editar: Callable[[int], None],
        on_eliminar: Callable[[int], None],
    ) -> None:
        self._on_editar = on_editar
        self._on_eliminar = on_eliminar

        super().__init__(
            columns=[
                ft.DataColumn(ft.Text(
                    c, size=11, weight=ft.FontWeight.W_600,
                    font_family=Fuentes.CAMPOS, color=Colores.BLANCO,
                ))
                for c in self._COLUMNAS
            ],
            rows=[],
            heading_row_color=Colores.AZUL_PRIMARIO,
            heading_row_height=36,
            data_row_max_height=36,
            column_spacing=12,
            horizontal_margin=10,
            border=ft.border.all(1, Colores.BORDE),
            border_radius=6,
            expand=True,
        )

    # ── API pública ───────────────────────────────────────────

    def cargar(self, registros: list) -> None:
        """Reconstruye las filas de la tabla con los registros dados.

        Args:
            registros: Lista de HorarioRegistradoDTO.
        """
        self.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(
                    str(i).zfill(3), size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Text(
                    r.semestre, size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Text(
                    r.unidad, size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Text(
                    r.docente, size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Text(
                    str(r.total_horas), size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Text(
                    r.aulas, size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Text(
                    r.periodo, size=12,
                    font_family=Fuentes.CAMPOS, color=Colores.TEXTO,
                )),
                ft.DataCell(ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=Colores.AZUL_PRIMARIO,
                        icon_size=16, tooltip="Editar",
                        on_click=partial(self._editar_click, r.id_horario),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=Colores.ROJO,
                        icon_size=16, tooltip="Eliminar",
                        on_click=partial(self._eliminar_click, r.id_horario),
                    ),
                ], spacing=0)),
            ])
            for i, r in enumerate(registros, start=1)
        ]
        if self.page:
            self.update()

    def limpiar(self) -> None:
        """Vacía la tabla."""
        self.rows = []
        if self.page:
            self.update()

    # ── Callbacks internos ────────────────────────────────────

    def _editar_click(self, id_horario: int, _=None) -> None:
        self._on_editar(id_horario)

    def _eliminar_click(self, id_horario: int, _=None) -> None:
        self._on_eliminar(id_horario)
