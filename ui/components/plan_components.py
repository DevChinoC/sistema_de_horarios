import flet as ft
from typing import Callable


# ════════════════════════════════════════════════════════════
# Tokens de diseño
# ════════════════════════════════════════════════════════════
class Colores:
    AZUL_PRIMARIO = "#2563EB"
    AZUL_HOVER    = "#1D4ED8"
    ROJO          = "#DC2626"
    BLANCO        = "#FFFFFF"
    BORDE         = "#0A0A0A"
    TEXTO         = "#1E293B"
    TEXTO_MUTED   = "#64748B"
    FONDO_TABLA   = "#F8FAFC"
    FONDO_APP     = "#E5E7EB"


class Fuentes:
    TITULO  = "Adamina"
    BOTONES = "Inter"
    CAMPOS  = "Roboto Condensed"


# ════════════════════════════════════════════════════════════
# Utilidad: opción de dropdown con texto negro sólido
# ════════════════════════════════════════════════════════════
def _opcion(key: str, text: str) -> ft.dropdown.Option:
    """Crea un dropdown.Option con texto siempre negro y legible."""
    return ft.dropdown.Option(
        key=key,
        text=text,
        text_style=ft.TextStyle(color="#000000", font_family=Fuentes.CAMPOS),
    )


# ════════════════════════════════════════════════════════════
# Botón primario reutilizable
# ════════════════════════════════════════════════════════════
class BotonPrimario(ft.ElevatedButton):
    def __init__(self, texto: str, on_click: Callable,
                 color: str = Colores.AZUL_PRIMARIO):
        super().__init__(
            text=texto, on_click=on_click,
            bgcolor=color, color=Colores.BLANCO,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.symmetric(horizontal=50, vertical=14),
                text_style=ft.TextStyle(
                    size=16, weight=ft.FontWeight.BOLD,
                    font_family=Fuentes.BOTONES,
                ),
            ),
            elevation=0,
        )


# ════════════════════════════════════════════════════════════
# Header 
# ════════════════════════════════════════════════════════════
class CabeceraPlan(ft.Container):
    """Icono | Título centrado | X roja cuadrada."""

    def __init__(self, on_cerrar: Callable) -> None:
        icono = ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED,
                        color=Colores.AZUL_PRIMARIO, size=32)
        titulo = ft.Text(
            "Crear plan de estudios",
            size=24, weight=ft.FontWeight.W_400,
            color=Colores.AZUL_PRIMARIO,
            font_family=Fuentes.TITULO,
            text_align=ft.TextAlign.CENTER,
            expand=True,
        )
        boton_x = ft.IconButton(
            icon=ft.Icons.CLOSE, icon_color=Colores.BLANCO,
            bgcolor=Colores.ROJO, icon_size=18, on_click=on_cerrar,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),   # cuadrado
                padding=ft.padding.all(8),
            ),
        )
        super().__init__(
            content=ft.Row(
                controls=[icono, titulo, boton_x],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=Colores.BLANCO,
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            border=ft.border.only(bottom=ft.BorderSide(3, Colores.AZUL_PRIMARIO)),
        )


# ════════════════════════════════════════════════════════════
# Selector de Grado
# ════════════════════════════════════════════════════════════
class SelectorGrado(ft.Row):
    """Botones toggle por nivel académico + botón OTROS."""

    def __init__(
        self,
        niveles: list[dict],
        on_change: Callable[[str, int | None], None],
        on_crear_nivel: Callable[[str], dict | None] | None = None,
    ) -> None:
        self._on_change       = on_change
        self._on_crear_nivel  = on_crear_nivel
        self._niveles         = list(niveles)
        self._seleccionado    = self._niveles[0]["nombre"] if self._niveles else ""
        self._id_seleccionado = self._niveles[0]["id"]     if self._niveles else None
        self._botones: list[ft.OutlinedButton] = []
        self._mostrando_input = False

        self._input_nuevo = ft.TextField(
            hint_text="Nuevo grado...",
            border_color=Colores.BORDE,
            focused_border_color=Colores.AZUL_PRIMARIO,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=4),
            text_size=13, width=130,
            text_style=ft.TextStyle(font_family=Fuentes.CAMPOS),
            on_submit=self._confirmar_nuevo,
            visible=False,
        )
        self._btn_confirmar = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE, icon_color=Colores.AZUL_PRIMARIO,
            icon_size=20, on_click=self._confirmar_nuevo,
            visible=False, tooltip="Agregar",
        )
        self._btn_cancelar_input = ft.IconButton(
            icon=ft.Icons.CANCEL, icon_color=Colores.ROJO,
            icon_size=20, on_click=self._cancelar_nuevo,
            visible=False, tooltip="Cancelar",
        )

        super().__init__(
            controls=[
                ft.Text("Grado:", size=14, weight=ft.FontWeight.W_600,
                        color=Colores.TEXTO, font_family=Fuentes.CAMPOS),
                *self._crear_botones(),
                self._input_nuevo,
                self._btn_confirmar,
                self._btn_cancelar_input,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        )

    def _crear_botones(self) -> list[ft.OutlinedButton]:
        self._botones.clear()
        for nivel in self._niveles:
            nombre = nivel["nombre"]
            activo = nombre == self._seleccionado
            btn = ft.OutlinedButton(
                text=nombre,
                on_click=lambda e, n=nivel: self._seleccionar(n),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=5),
                    padding=ft.padding.symmetric(horizontal=16, vertical=6),
                    bgcolor=Colores.AZUL_PRIMARIO if activo else "transparent",
                    color=Colores.BLANCO if activo else Colores.AZUL_PRIMARIO,
                    side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                    text_style=ft.TextStyle(font_family=Fuentes.TITULO),
                ),
            )
            self._botones.append(btn)

        btn_otros = ft.OutlinedButton(
            text="OTROS",
            on_click=lambda _: self._mostrar_input_nuevo(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5),
                padding=ft.padding.symmetric(horizontal=16, vertical=6),
                bgcolor="transparent", color=Colores.AZUL_PRIMARIO,
                side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                text_style=ft.TextStyle(font_family=Fuentes.TITULO),
            ),
        )
        self._btn_otros = btn_otros
        self._botones.append(btn_otros)
        return self._botones

    def _seleccionar(self, nivel: dict) -> None:
        self._seleccionado    = nivel["nombre"]
        self._id_seleccionado = nivel["id"]
        self._actualizar_estilos()
        self._on_change(nivel["nombre"], nivel["id"])

    def _actualizar_estilos(self) -> None:
        for btn in self._botones:
            if btn is self._btn_otros:
                btn.style.bgcolor = "transparent"
                btn.style.color   = Colores.AZUL_PRIMARIO
            else:
                activo = btn.text == self._seleccionado
                btn.style.bgcolor = Colores.AZUL_PRIMARIO if activo else "transparent"
                btn.style.color   = Colores.BLANCO if activo else Colores.AZUL_PRIMARIO
        if self.page:
            self.update()

    def _mostrar_input_nuevo(self) -> None:
        if self._mostrando_input:
            return
        self._mostrando_input            = True
        self._input_nuevo.visible        = True
        self._btn_confirmar.visible      = True
        self._btn_cancelar_input.visible = True
        if self.page:
            self.update()
            self._input_nuevo.focus()

    def _cancelar_nuevo(self, _=None) -> None:
        self._mostrando_input            = False
        self._input_nuevo.value          = ""
        self._input_nuevo.visible        = False
        self._btn_confirmar.visible      = False
        self._btn_cancelar_input.visible = False
        if self.page:
            self.update()

    def _confirmar_nuevo(self, _=None) -> None:
        nombre = (self._input_nuevo.value or "").strip().upper()
        if not nombre:
            return
        for n in self._niveles:
            if n["nombre"].upper() == nombre:
                self._seleccionar(n)
                self._cancelar_nuevo()
                return
        if self._on_crear_nivel:
            nuevo = self._on_crear_nivel(nombre)
            if nuevo is None:
                return
            self._niveles.append(nuevo)
            nuevo_btn = ft.OutlinedButton(
                text=nuevo["nombre"],
                on_click=lambda e, nv=nuevo: self._seleccionar(nv),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=5),
                    padding=ft.padding.symmetric(horizontal=16, vertical=6),
                    bgcolor=Colores.AZUL_PRIMARIO, color=Colores.BLANCO,
                    side=ft.BorderSide(1.5, Colores.AZUL_PRIMARIO),
                    text_style=ft.TextStyle(font_family=Fuentes.TITULO),
                ),
            )
            idx      = self._botones.index(self._btn_otros)
            idx_ctrl = self.controls.index(self._btn_otros)
            self._botones.insert(idx, nuevo_btn)
            self.controls.insert(idx_ctrl, nuevo_btn)
            self._seleccionado    = nuevo["nombre"]
            self._id_seleccionado = nuevo["id"]
            self._actualizar_estilos()
            self._cancelar_nuevo()

    @property
    def valor(self) -> str:
        return self._seleccionado

    @property
    def id_valor(self) -> int | None:
        return self._id_seleccionado


# ════════════════════════════════════════════════════════════
# Diálogo de confirmación
# ════════════════════════════════════════════════════════════
class DialogoConfirmacion(ft.AlertDialog):
    def __init__(self, page: ft.Page, on_confirmar: Callable,
                 on_cancelar: Callable | None = None):
        self._page         = page
        self._on_confirmar = on_confirmar
        self._on_cancelar  = on_cancelar
        super().__init__(
            modal=True, bgcolor=Colores.ROJO,
            shape=ft.RoundedRectangleBorder(radius=10),
            title=ft.Text("¿Estás seguro?", size=18, weight=ft.FontWeight.W_600,
                          color=Colores.BLANCO, font_family=Fuentes.CAMPOS,
                          text_align=ft.TextAlign.CENTER),
            title_padding=ft.padding.only(top=24, left=24, right=24, bottom=8),
            actions=[
                ft.ElevatedButton(
                    text="Sí", bgcolor=Colores.ROJO, color=Colores.BLANCO,
                    on_click=self._si,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.padding.symmetric(horizontal=30, vertical=12),
                        text_style=ft.TextStyle(
                            size=14, weight=ft.FontWeight.BOLD,
                            font_family=Fuentes.BOTONES),
                    ), elevation=0,
                ),
                ft.ElevatedButton(
                    text="No", bgcolor=Colores.ROJO, color=Colores.BLANCO,
                    on_click=self._no,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        padding=ft.padding.symmetric(horizontal=30, vertical=12),
                        text_style=ft.TextStyle(
                            size=14, weight=ft.FontWeight.BOLD,
                            font_family=Fuentes.BOTONES),
                    ), elevation=0,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            actions_padding=ft.padding.only(bottom=20, top=4),
        )

    def _si(self, _=None):
        self._page.close(self)
        self._on_confirmar()

    def _no(self, _=None):
        self._page.close(self)
        if self._on_cancelar:
            self._on_cancelar()


# ════════════════════════════════════════════════════════════
# Fila de materia
# ════════════════════════════════════════════════════════════
class FilaMateriaControl:


    ID_TIPO_OPTATIVA = 2

    # Listas de opciones — construidas una sola vez a nivel de clase
    _OPTS_TRONCO   = [_opcion(str(i), f"{i}°") for i in range(1, 9)]
    _OPTS_OPTATIVA = [_opcion("0", "Semestre 0 (Optativa)")]

    def __init__(
        self,
        tipos: list[dict],
        nombre_inicial: str = "",
        id_tipo_inicial: int = 0,
        semestre_inicial: int = 0,
    ) -> None:

        _dd_base = dict(
            border_color         = Colores.BORDE,
            focused_border_color = Colores.AZUL_PRIMARIO,
            bgcolor              = Colores.BLANCO,
            fill_color           = Colores.BLANCO,
            color                = "#000000",
            content_padding      = ft.padding.symmetric(horizontal=8, vertical=2),
            text_size            = 12,
            text_style           = ft.TextStyle(
                color="#000000", font_family=Fuentes.CAMPOS),
        )

        self.campo_nombre = ft.TextField(
            value                = "",
            hint_text            = "Nombre de la materia...",
            hint_style           = ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            border_color         = Colores.BORDE,
            focused_border_color = Colores.AZUL_PRIMARIO,
            bgcolor              = Colores.BLANCO,
            color                = "#000000",
            content_padding      = ft.padding.symmetric(horizontal=8, vertical=6),
            text_size            = 12,
            expand               = True,
            text_style           = ft.TextStyle(
                color="#000000", font_family=Fuentes.CAMPOS),
        )

        self.dropdown_tipo = ft.Dropdown(
            options    = [_opcion(str(t["id"]), t["nombre"]) for t in tipos],
            value      = str(id_tipo_inicial) if id_tipo_inicial else None,
            hint_text  = "Tipo",
            hint_style = ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            on_change  = self._on_tipo_cambiado,
            **_dd_base,
        )

        es_optativa = (id_tipo_inicial == self.ID_TIPO_OPTATIVA)
        self.dropdown_semestre = ft.Dropdown(
            options    = list(self._OPTS_OPTATIVA) if es_optativa
                         else list(self._OPTS_TRONCO),
            value      = "0" if es_optativa
                         else (str(semestre_inicial) if semestre_inicial > 0 else None),
            disabled   = es_optativa,
            hint_text  = "Semestre",
            hint_style = ft.TextStyle(
                color=Colores.TEXTO_MUTED, font_family=Fuentes.CAMPOS),
            **_dd_base,
        )

        self._contenedor_fila: ft.Container | None = None

    def _on_tipo_cambiado(self, _) -> None:
        val = self.dropdown_tipo.value
        if val and int(val) == self.ID_TIPO_OPTATIVA:
            self.dropdown_semestre.options  = list(self._OPTS_OPTATIVA)
            self.dropdown_semestre.value    = "0"
            self.dropdown_semestre.disabled = True
        else:
            self.dropdown_semestre.options  = list(self._OPTS_TRONCO)
            self.dropdown_semestre.value    = None
            self.dropdown_semestre.disabled = False
        if self.dropdown_semestre.page:
            self.dropdown_semestre.update()

    def obtener_datos(self) -> dict | None:
        n = (self.campo_nombre.value or "").strip()
        t = self.dropdown_tipo.value
        s = self.dropdown_semestre.value
        if not n or not t:
            return None
        id_tipo = int(t)
        if id_tipo == self.ID_TIPO_OPTATIVA:
            sem = 0
        else:
            if not s or s == "0":
                return None
            sem = int(s)
            if not 1 <= sem <= 8:
                return None
        return {"nombre_materia": n, "id_tipo": id_tipo, "numero_semestre": sem}


# ════════════════════════════════════════════════════════════
# Tabla de materias — ancho fijo, scroll acotado
# ════════════════════════════════════════════════════════════
class TablaMaterias(ft.Column):

    ANCHO_TABLA  = 520
    ALTURA_FILAS = 200

    def __init__(self, tipos: list[dict]) -> None:
        self._tipos = tipos
        self._filas: list[FilaMateriaControl] = []

        w_n = int(self.ANCHO_TABLA * 0.54)
        w_t = int(self.ANCHO_TABLA * 0.22)
        w_s = self.ANCHO_TABLA - w_n - w_t
        self._w_n, self._w_t, self._w_s = w_n, w_t, w_s

        cabecera = ft.Container(
            width=self.ANCHO_TABLA,
            bgcolor=Colores.AZUL_PRIMARIO,
            padding=ft.padding.symmetric(horizontal=0, vertical=8),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
            content=ft.Row(
                spacing=0,
                controls=[
                    ft.Container(width=w_n, content=ft.Text(
                        "Nombre", color=Colores.BLANCO, size=13,
                        weight=ft.FontWeight.W_500, font_family=Fuentes.CAMPOS,
                        text_align=ft.TextAlign.CENTER)),
                    ft.Container(width=w_t, content=ft.Text(
                        "Tipo", color=Colores.BLANCO, size=13,
                        weight=ft.FontWeight.W_500, font_family=Fuentes.CAMPOS,
                        text_align=ft.TextAlign.CENTER)),
                    ft.Container(width=w_s, content=ft.Text(
                        "Semestre", color=Colores.BLANCO, size=13,
                        weight=ft.FontWeight.W_500, font_family=Fuentes.CAMPOS,
                        text_align=ft.TextAlign.CENTER)),
                ],
            ),
        )

        self._col_filas = ft.Column(controls=[], spacing=0,
                                    scroll=ft.ScrollMode.AUTO)
        area_scroll = ft.Container(
            content=self._col_filas,
            width=self.ANCHO_TABLA,
            height=self.ALTURA_FILAS,
            bgcolor=Colores.BLANCO,
            border=ft.border.only(
                left=ft.BorderSide(1, Colores.BORDE),
                right=ft.BorderSide(1, Colores.BORDE),
                bottom=ft.BorderSide(1, Colores.BORDE),
            ),
            border_radius=ft.border_radius.only(
                bottom_left=5, bottom_right=5),
        )

        btn_add = ft.ElevatedButton(
            text="+",
            on_click=lambda _: self.agregar_fila(),
            bgcolor=Colores.AZUL_PRIMARIO, color=Colores.BLANCO,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=5),
                padding=ft.padding.all(0),
                text_style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD),
            ),
            width=34, height=34, elevation=0,
        )
        fila_btn = ft.Container(
            width=self.ANCHO_TABLA,
            content=ft.Row(controls=[btn_add],
                           alignment=ft.MainAxisAlignment.END),
        )

        super().__init__(
            controls=[fila_btn, cabecera, area_scroll],
            spacing=0,
        )

    def agregar_fila(self, nombre: str = "",
                     id_tipo: int = 0, semestre: int = 0) -> None:
        fila = FilaMateriaControl(self._tipos, nombre, id_tipo, semestre)
        self._filas.append(fila)

        contenedor = ft.Container(
            bgcolor=Colores.BLANCO,
            border=ft.border.only(bottom=ft.BorderSide(1, Colores.BORDE)),
            padding=ft.padding.symmetric(horizontal=0, vertical=2),
            content=ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=self._w_n,
                                 padding=ft.padding.only(left=6, right=4),
                                 content=fila.campo_nombre),
                    ft.Container(width=self._w_t,
                                 content=fila.dropdown_tipo),
                    ft.Container(width=self._w_s,
                                 content=fila.dropdown_semestre),
                ],
            ),
        )
        fila._contenedor_fila = contenedor
        self._col_filas.controls.append(contenedor)
        if self.page:
            self._col_filas.update()

    def obtener_filas(self) -> list[dict]:
        return [d for f in self._filas if (d := f.obtener_datos())]
