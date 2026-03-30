import flet as ft
from ui.views.plan_view import build_plan_view


def main(page: ft.Page):
    page.title              = "Sistema de Horarios"
    page.window.width       = 1200
    page.window.height      = 700
    page.window.min_width   = 800    
    page.window.min_height  = 500
    page.window.resizable   = True
    page.window.maximizable = True
    page.window.maximized   = False  
    page.padding = 0

    try:
        view = build_plan_view(page)
        page.add(view)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, color="#F01E1E", size=48),
                        ft.Text(f"Error al iniciar:\n{ex}",
                                color="#F01E1E", text_align=ft.TextAlign.CENTER),
                    ],
                ),
            )
        )

    page.window.visible = True
    page.update()


if __name__ == "__main__":
    ft.app(target=main)