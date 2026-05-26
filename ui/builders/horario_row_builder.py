"""
Builder de filas de la tabla de horarios.

Construye ft.DataRow con celdas de texto y botones de acción.

SOLO UI: construye widgets. No contiene lógica de negocio.
"""
from __future__ import annotations

from functools import partial
from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes


class HorarioRowBuilder:
    """Construye ft.DataRow para la tabla de horarios registrados.

    Uso:
        row = HorarioRowBuilder.build(registro, indice=1, on_editar=..., on_eliminar=...)
    """

    @staticmethod
    def build(
        registro,
        indice: int,
        on_editar: Callable[[int], None],
        on_eliminar: Callable[[int], None],
    ) -> ft.DataRow:
        """Crea un DataRow a partir de un HorarioRegistradoDTO.

        Args:
            registro: HorarioRegistradoDTO con los datos del horario.
            indice: Número de fila para mostrar como clave (001, 002…).
            on_editar: Callback al presionar editar (recibe id_horario).
            on_eliminar: Callback al presionar eliminar (recibe id_horario).
        """
        def _cell(texto: str) -> ft.DataCell:
            return ft.DataCell(ft.Text(
                str(texto),
                size=12,
                font_family=Fuentes.CAMPOS,
                color=Colores.TEXTO,
            ))

        return ft.DataRow(cells=[
            _cell(str(indice).zfill(3)),
            _cell(registro.semestre),
            _cell(registro.unidad),
            _cell(registro.docente),
            _cell(registro.total_horas),
            _cell(registro.aulas),
            _cell(registro.periodo),
            ft.DataCell(
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=Colores.AZUL_PRIMARIO,
                        icon_size=16,
                        tooltip="Editar",
                        on_click=partial(
                            lambda id_d, _: on_editar(id_d),
                            registro.id_detalle_horario,
                        ),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        icon_color=Colores.ROJO,
                        icon_size=16,
                        tooltip="Eliminar",
                        on_click=partial(
                            lambda id_h, _: on_eliminar(id_h),
                            registro.id_horario,
                        ),
                    ),
                ], spacing=0),
            ),
        ])

    @staticmethod
    def build_many(
        registros: list,
        on_editar: Callable[[int], None],
        on_eliminar: Callable[[int], None],
    ) -> list[ft.DataRow]:
        """Construye la lista completa de DataRows para la tabla.

        Args:
            registros: Lista de HorarioRegistradoDTO.
            on_editar: Callback al presionar editar.
            on_eliminar: Callback al presionar eliminar.
        """
        return [
            HorarioRowBuilder.build(r, i, on_editar, on_eliminar)
            for i, r in enumerate(registros, start=1)
        ]
