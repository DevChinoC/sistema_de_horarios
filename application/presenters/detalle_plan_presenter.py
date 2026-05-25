"""
Presenter de DetallePlan.

Coordina la apertura de diálogos modales, confirmaciones y mensajes
de la pantalla de detalle de plan.

RESPONSABILIDAD: UI coordinada (abrir/cerrar diálogos).
NO contiene: lógica de negocio, acceso a BD, transformaciones complejas.
"""
from __future__ import annotations

import os
import tempfile
import time as _time
from typing import Callable

import flet as ft

from ui.components.plan_components import Colores, Fuentes, DialogoConfirmacion


class DetallePlanPresenter:
    """Coordina diálogos y mensajes de la pantalla DetallePlan.

    Uso:
        presenter = DetallePlanPresenter(page)
        presenter.confirmar_eliminar(on_confirmar=lambda: ...)
        presenter.mostrar_preview_pdf(ruta_pdf)
    """

    def __init__(self, page: ft.Page) -> None:
        self._page = page

    # ── Confirmaciones ────────────────────────────────────────

    def confirmar_eliminar(self, on_confirmar: Callable) -> None:
        """Muestra diálogo '¿Estás seguro?' antes de eliminar un horario."""
        self._page.open(DialogoConfirmacion(
            page=self._page,
            on_confirmar=on_confirmar,
        ))

    def confirmar_cancelar_edicion(self, on_confirmar: Callable) -> None:
        """Muestra diálogo de confirmación para cancelar la edición en curso."""
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=Colores.BLANCO,
            title=ft.Text(
                "¿Cancelar edición?",
                font_family=Fuentes.TITULO,
                size=17,
                color=Colores.TEXTO,
            ),
            content=ft.Text(
                "Los cambios no guardados se perderán.",
                size=13,
                color=Colores.TEXTO,
                font_family=Fuentes.CAMPOS,
            ),
            actions=[
                ft.TextButton(
                    "No, seguir editando",
                    on_click=lambda _: self._page.close(dlg),
                    style=ft.ButtonStyle(color=Colores.TEXTO),
                ),
                ft.ElevatedButton(
                    "Sí, cancelar",
                    bgcolor=Colores.ROJO,
                    color=Colores.BLANCO,
                    elevation=0,
                    on_click=lambda _: (self._page.close(dlg), on_confirmar()),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        self._page.open(dlg)

    # ── Preview PDF ───────────────────────────────────────────

    def mostrar_preview_pdf(self, ruta_pdf: str) -> None:
        """Muestra vista previa del PDF en un diálogo modal.

        Si PyMuPDF no está instalado, abre el archivo con el visor del sistema.
        """
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(ruta_pdf)
            pix = doc[0].get_pixmap(dpi=150)
            ts = int(_time.time())
            img_path = os.path.join(
                tempfile.gettempdir(), f"preview_{ts}.png",
            )
            pix.save(img_path)
            doc.close()
            self._mostrar_imagen_pdf(img_path)
        except ImportError:
            self._abrir_visor_sistema(ruta_pdf)

    def _mostrar_imagen_pdf(self, img_path: str) -> None:
        """Muestra la imagen de la primera página del PDF en un diálogo."""
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=Colores.BLANCO,
            title=ft.Text(
                "Vista previa del documento",
                font_family=Fuentes.TITULO,
                size=18,
                color=Colores.AZUL_PRIMARIO,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Image(
                            src=img_path,
                            fit=ft.ImageFit.CONTAIN,
                            width=550,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                width=600,
                height=550,
                border=ft.border.all(1, Colores.AZUL_PRIMARIO),
                border_radius=8,
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda _: self._page.close(dlg),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        self._page.open(dlg)

    def _abrir_visor_sistema(self, ruta: str) -> None:
        """Abre el archivo con el visor del sistema operativo."""
        import subprocess, sys
        if sys.platform.startswith("win"):
            os.startfile(ruta)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])

    # ── Mensajes ──────────────────────────────────────────────

    def mensaje(self, texto: str) -> None:
        """Muestra un SnackBar con el texto dado."""
        print(f"[DetallePlanPresenter] {texto}")
        self._page.open(ft.SnackBar(content=ft.Text(texto)))

    def mensaje_error(self, texto: str, titulo: str = "Error") -> None:
        """Muestra un AlertDialog de error."""
        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=Colores.BLANCO,
            title=ft.Row([
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=Colores.ROJO),
                ft.Text(titulo, color=Colores.ROJO, font_family=Fuentes.TITULO, size=16),
            ], spacing=8),
            content=ft.Text(texto, size=13, color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
            actions=[
                ft.ElevatedButton(
                    "Cerrar",
                    on_click=lambda _: self._page.close(dlg),
                    bgcolor=Colores.AZUL_PRIMARIO,
                    color=Colores.BLANCO,
                    elevation=0,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        self._page.open(dlg)
