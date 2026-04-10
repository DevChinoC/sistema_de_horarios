import flet as ft
import threading
import time
from typing import Callable


class PuertaAnimada(ft.Container):
    """Puerta que al hacer clic anima su apertura y navega a otra vista.

    La animación comprime la escala horizontal (1.0 → 0.0) simulando
    que la puerta gira sobre su eje izquierdo al abrirse.
    Se necesita did_mount para que la animación de Flet funcione
    correctamente (el widget debe estar montado antes de cambiar scale).
    """

    _DURACION_MS = 500

    def __init__(self, on_abrir: Callable) -> None:
        self._on_abrir = on_abrir
        self._abierta  = False

        self._imagen = ft.Image(
            src="https://em-content.zobj.net/source/microsoft/379/door_1f6aa.png",
            width=110,
            height=130,
            fit=ft.ImageFit.CONTAIN,
        )

        # El Container interno es el que tiene animate_scale
        self._puerta_ct = ft.Container(
            content=self._imagen,
            width=110,
            height=130,
            alignment=ft.alignment.center_left,
            animate_scale=ft.Animation(
                self._DURACION_MS, ft.AnimationCurve.EASE_IN_OUT),
            scale=ft.Scale(scale_x=1.0, scale_y=1.0),
        )

        super().__init__(
            content=self._puerta_ct,
            on_click=self._animar_apertura,
            tooltip="Haz clic para abrir",
            width=120,
            height=140,
        )

    # ── API pública ───────────────────────────────────────────

    def resetear(self) -> None:
        """Restaura la puerta a estado cerrado."""
        self._abierta = False
        self._puerta_ct.scale = ft.Scale(scale_x=1.0, scale_y=1.0)
        if self.page:
            self._puerta_ct.update()

    # ── Lógica interna ────────────────────────────────────────

    def _animar_apertura(self, _) -> None:
        if self._abierta:
            return
        self._abierta = True
        # Escala a 0 en X → puerta se "cierra perspectivalmente"
        self._puerta_ct.scale = ft.Scale(scale_x=0.0, scale_y=1.0)
        self._puerta_ct.update()
        # Navegar después de que termina la animación
        threading.Thread(target=self._navegar_tras_espera, daemon=True).start()

    def _navegar_tras_espera(self) -> None:
        time.sleep(self._DURACION_MS / 1000 + 0.15)
        if self._on_abrir:
            self._on_abrir()
