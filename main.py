import flet as ft
from application.services.plan_estudios_service import PlanEstudiosService
from ui.views.crear_plan_view import CrearPlanView
from ui.components.plan_components import Colores, Fuentes


def main(page: ft.Page) -> None:
    page.title = "Sistema de Horarios"
    page.window.width = 900
    page.window.height = 700
    page.padding = 0
    page.bgcolor = Colores.BLANCO

    page.fonts = {
        Fuentes.TITULO:  "https://raw.githubusercontent.com/google/fonts/main/ofl/adamina/Adamina-Regular.ttf",
        Fuentes.BOTONES: "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
        Fuentes.CAMPOS:  "https://raw.githubusercontent.com/google/fonts/main/ofl/robotocondensed/RobotoCondensed%5Bwght%5D.ttf",
    }

    service = PlanEstudiosService()

    lies_lista = service.obtener_lies()
    lies_activa = lies_lista[0] if lies_lista else {"id": 1, "nombre": "TICs"}

    vista = CrearPlanView(
        page=page,
        service=service,
        lies_activa=lies_activa,
        on_guardado=lambda: print("Plan guardado exitosamente."),
        on_cancelado=lambda: print("Cancelado — preparado para navegar a otra pantalla."),
    )

    page.add(vista)


ft.app(target=main)