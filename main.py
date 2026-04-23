import flet as ft

from application.services.planes_service import PlanesService
from application.services.plan_estudios_service import PlanEstudiosService
from application.services.horario_service import HorarioService
from ui.components.plan_components import Colores, Fuentes
from ui.navigation.navegador import Navegador


def main(page: ft.Page) -> None:
    # ── Configuración de la ventana ───────────────────────────
    page.title         = "Sistema de Horarios"
    page.window.width  = 1920
    page.window.height = 1080
    page.padding       = 0
    page.bgcolor       = Colores.BLANCO

    # ── Tema global: dropdowns con fondo blanco y texto negro ─
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            surface=Colores.BLANCO,
            on_surface="#000000",
            surface_variant=Colores.BLANCO,
            on_surface_variant="#000000",
        ),
    )

    # ── Fuentes ───────────────────────────────────────────────
    page.fonts = {
        Fuentes.TITULO:  "https://raw.githubusercontent.com/google/fonts/main/ofl/adamina/Adamina-Regular.ttf",
        Fuentes.BOTONES: "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
        Fuentes.CAMPOS:  "https://raw.githubusercontent.com/google/fonts/main/ofl/robotocondensed/RobotoCondensed%5Bwght%5D.ttf",
    }

    # ── Navegación ────────────────────────────────────────────
    nav = Navegador(
        page=page,
        planes_service=PlanesService(),
        plan_service=PlanEstudiosService(),
        horario_service=HorarioService(),
    )
    nav.ir_a_planes()


ft.app(target=main, assets_dir="ui/assets")
