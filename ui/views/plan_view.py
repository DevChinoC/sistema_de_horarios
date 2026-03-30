import flet as ft
import threading
import time
from infrastructure.db.connection import SessionLocal
from infrastructure.repositories.plan_repository import PlanRepository

# ─── COLORES ────────────────────────────────────────────────────────────────
AZUL      = "#3D5FD2"
ROJO      = "#F01E1E"
NEGRO     = "#000000"
BLANCO    = "#FFFFFF"
BORDE     = "#AAAAAA"

# ─── TIPOGRAFÍAS ─────────────────────────────────────────────────────────────
F_ADAMINA  = "Adamina"
F_ROBOTO_C = "RobotoCondensed"
F_INTER    = "Inter"

# ─── TAMAÑO ÚNICO DE TEXTO ───────────────────────────────
TS = 13   


# ─── ANCHOS FIJOS TABLA ──────────────────────────────────────────────────────
W_NOMBRE   = 330
W_TIPO     = 100
W_SEMESTRE = 140
W_TABLA    = W_NOMBRE + W_TIPO + W_SEMESTRE   # 570

H_FILAS_MAX = 210


def _opt(key: str, text: str = None) -> ft.dropdown.Option:
    """Opción de dropdown con texto negro forzado."""
    label = text or key
    return ft.dropdown.Option(
        key     = key,
        content = ft.Text(label, color=NEGRO, font_family=F_ROBOTO_C, size=TS),
    )


def build_plan_view(page: ft.Page):
    page.bgcolor = BLANCO
    page.padding = 0

    # ── FUENTES GOOGLE ────────────────────────────────────────────────────────
    page.fonts = {
        F_ADAMINA:  "https://fonts.gstatic.com/s/adamina/v27/j8_r6-DH1bjoc-dwu-reIgiUU7E.ttf",
        F_ROBOTO_C: "https://fonts.gstatic.com/s/robotocondensed/v27/ieVl2ZhZI2eCN5jzbjEETS9weererBpDqU-bsg.ttf",
        F_INTER:    "https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2",
    }

    # ── BD ───────────────────────────────────────────────────────────────────
    try:
        _db        = SessionLocal()
        _repo      = PlanRepository(_db)
        niveles_bd = list(_repo.obtener_niveles())
    except Exception:
        _db        = None
        _repo      = None
        niveles_bd = []

    nivel_sel = {"id": niveles_bd[0][0] if niveles_bd else 1}

    # ── ESTILO BOTÓN NIVEL ───────────────────────────────────────────────────
    def _estilo_btn(activo: bool) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            bgcolor  = {ft.ControlState.DEFAULT: AZUL   if activo else BLANCO},
            color    = {ft.ControlState.DEFAULT: BLANCO if activo else AZUL},
            side     = ft.BorderSide(2, AZUL),
            shape    = ft.RoundedRectangleBorder(radius=6),
            padding  = ft.padding.symmetric(horizontal=14, vertical=6),
        )

    btn_refs: dict = {}

    def seleccionar_nivel(nid: int):
        nivel_sel["id"] = nid
        for k, b in btn_refs.items():
            b.style = _estilo_btn(k == nid)
        page.update()

    def _crear_btn_nivel(nid: int, nombre: str, activo: bool = False) -> ft.ElevatedButton:
        b = ft.ElevatedButton(
            content  = ft.Text(nombre, font_family=F_ADAMINA, size=TS),
            style    = _estilo_btn(activo),
            on_click = lambda e, x=nid: seleccionar_nivel(x),
        )
        btn_refs[nid] = b
        return b

    # ── SLOT OTROS ───────────────────────────────────────────────────────────
    otros_slot = ft.Container()

    tf_otros = ft.TextField(
        hint_text       = "Ej: INGENIERÍA",
        width           = 150,
        height          = 34,
        border_color    = AZUL,
        border_radius   = 6,
        text_size       = TS,
        content_padding = ft.padding.symmetric(horizontal=8, vertical=2),
        text_style      = ft.TextStyle(font_family=F_ROBOTO_C, color=NEGRO, size=TS),
        capitalization  = ft.TextCapitalization.CHARACTERS,
    )

    def _confirmar_otros(e=None):
        nombre = (tf_otros.value or "").strip().upper()
        if nombre and _repo:
            try:
                nuevo_id = _repo.crear_nivel(nombre)
                btn_nuevo = _crear_btn_nivel(nuevo_id, nombre, activo=True)
                nivel_sel["id"] = nuevo_id
                for k, b in btn_refs.items():
                    b.style = _estilo_btn(k == nuevo_id)
                pos = len(fila_botones.controls) - 1
                fila_botones.controls.insert(pos, btn_nuevo)
            except Exception:
                pass
        tf_otros.value = ""
        _modo_boton()

    def _cancelar_otros(e=None):
        tf_otros.value = ""
        _modo_boton()

    tf_otros.on_submit = _confirmar_otros

    btn_ok = ft.IconButton(
        icon=ft.Icons.CHECK_CIRCLE_OUTLINE, icon_color=AZUL,
        icon_size=18, tooltip="Agregar", on_click=_confirmar_otros,
        style=ft.ButtonStyle(padding=ft.padding.all(2)),
    )
    btn_cancel = ft.IconButton(
        icon=ft.Icons.CLOSE, icon_color=ROJO,
        icon_size=16, tooltip="Cancelar", on_click=_cancelar_otros,
        style=ft.ButtonStyle(padding=ft.padding.all(2)),
    )

    _btn_otros = ft.OutlinedButton(
        content  = ft.Text("+ OTROS", font_family=F_ADAMINA, size=TS, color=AZUL),
        style    = ft.ButtonStyle(
            color   = AZUL,
            side    = ft.BorderSide(2, AZUL),
            shape   = ft.RoundedRectangleBorder(radius=6),
            padding = ft.padding.symmetric(horizontal=14, vertical=6),
        ),
        on_click = lambda e: _modo_input(),
    )

    def _modo_boton():
        otros_slot.content = _btn_otros
        if page.controls:
            page.update()

    def _modo_input():
        otros_slot.content = ft.Row(
            spacing=4,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[tf_otros, btn_ok, btn_cancel],
        )
        page.update()
        tf_otros.focus()
        page.update()

    
    otros_slot.content = _btn_otros

    # ── FILA GRADO ───────────────────────────────────────────────────────────
    fila_botones = ft.Row(
        spacing            = 10,
        vertical_alignment = ft.CrossAxisAlignment.CENTER,
        controls           = [
            ft.Text("Grado:", weight=ft.FontWeight.BOLD,
                    size=TS, color=NEGRO, font_family=F_ROBOTO_C),
        ],
    )

    for idx, (nid, nombre) in enumerate(niveles_bd):
        b = _crear_btn_nivel(nid, nombre, activo=(idx == 0))
        if idx == 0:
            nivel_sel["id"] = nid
        fila_botones.controls.append(b)

    fila_botones.controls.append(otros_slot)

    # ── CAMPOS NOMBRE / FECHA ─────────────────────────────────────────────────
    _tf_style = dict(
        height          = 38,
        border_color    = BORDE,
        bgcolor         = BLANCO,
        text_size       = TS,
        border_radius   = 4,
        content_padding = ft.padding.symmetric(horizontal=10, vertical=6),
        text_style      = ft.TextStyle(font_family=F_ROBOTO_C, color=NEGRO, size=TS),
        hint_style      = ft.TextStyle(font_family=F_ROBOTO_C, color="#AAAAAA", size=TS),
    )
    f_nombre = ft.TextField(hint_text="Nombre del plan....", width=260, **_tf_style)
    f_fecha  = ft.TextField(hint_text="DD/MM/AA",           width=260, **_tf_style)

    # ── OPCIONES DROPDOWN ─────────────────────────────────────────────────────
    OPTS_TODO = [_opt(f"Semestre {i}") for i in range(0, 9)]
    OPTS_TIPO = [_opt("Tronco"), _opt("Optativa")]

    # ── FILAS TABLA (scroll interno) ──────────────────────────────────────────
    filas = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, height=H_FILAS_MAX)

    _dd_style = dict(
        dense      = True,
        bgcolor    = BLANCO,
        border     = ft.InputBorder.NONE,
        color      = NEGRO,
        text_style = ft.TextStyle(font_family=F_ROBOTO_C, color=NEGRO, size=TS),
    )

    def _nueva_fila() -> ft.Container:
        tf = ft.TextField(
            hint_text       = "Tecnologías de información y comunicación",
            border          = ft.InputBorder.NONE,
            text_size       = TS,
            content_padding = ft.padding.only(left=10),
            width           = W_NOMBRE,
            text_style      = ft.TextStyle(font_family=F_ROBOTO_C, color=NEGRO, size=TS),
            hint_style      = ft.TextStyle(font_family=F_ROBOTO_C, color="#AAAAAA", size=TS),
        )

        dd_sem = ft.Dropdown(
            value   = "Semestre",
            options = list(OPTS_TODO),
            width   = W_SEMESTRE,
            **_dd_style,
        )

        def _on_tipo(e):
            if dd_tipo.value == "Optativa":
                dd_sem.options = [_opt("Semestre 0")]
                dd_sem.value   = "Semestre 0"
                dd_sem.bgcolor = "#F0F0F0"
            else:
                dd_sem.options = [_opt(f"Semestre {i}") for i in range(0, 9)]
                dd_sem.value   = "Semestre"
                dd_sem.bgcolor = BLANCO
            page.update()

        dd_tipo = ft.Dropdown(
            value     = "Tipo",
            options   = list(OPTS_TIPO),
            on_change = _on_tipo,
            width     = W_TIPO,
            **_dd_style,
        )

        return ft.Container(
            height  = 42,
            bgcolor = BLANCO,
            border  = ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
            content = ft.Row(
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(width=W_NOMBRE, content=tf),
                    ft.Container(
                        width=W_TIPO,
                        border=ft.border.only(left=ft.BorderSide(1, "#E0E0E0")),
                        content=dd_tipo,
                    ),
                    ft.Container(
                        width=W_SEMESTRE,
                        border=ft.border.only(left=ft.BorderSide(1, "#E0E0E0")),
                        content=dd_sem,
                    ),
                ],
            ),
        )

    filas.controls.append(_nueva_fila())

    def _agregar_fila(e):
        filas.controls.append(_nueva_fila())
        page.update()

    # ── CONFIRMACIÓN CENTRADA ────────────────────────────────────────────────
    def _mostrar_exito(mensaje: str = "Plan guardado exitosamente"):
        overlay = ft.Container(
            expand=True,
            bgcolor="#99000000",
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.CHECK_CIRCLE, color="#22B14C", size=120),
        )
        page.overlay.append(overlay)
        page.update()

        def _cerrar():
            time.sleep(2)
            if overlay in page.overlay:
                page.overlay.remove(overlay)
                page.update()

        threading.Thread(target=_cerrar, daemon=True).start()

    # ── GUARDAR ──────────────────────────────────────────────────────────────
    def _guardar(e):
        if _repo is None:
            page.open(
                ft.SnackBar(
                    content=ft.Text("Sin conexión a base de datos",
                                    font_family=F_ROBOTO_C, size=TS),
                    bgcolor=ROJO,
                )
            )
            return
        try:
            # El plan engloba todas las LIES activas
            ids_lies = _repo.obtener_todas_lies()

            plan = _repo.crear_plan(f_nombre.value, nivel_sel["id"])
            _repo.vincular_plan_lies(plan.id_plan, ids_lies)
            _repo.crear_semestres_base(plan.id_plan)

            for fila in filas.controls:
                row   = fila.content.controls
                nom   = row[0].content.value.strip()
                tipo  = row[1].content.value
                sem_v = row[2].content.value
                num   = int(sem_v.split()[-1]) if sem_v and sem_v not in ("Semestre",) else 0
                id_s  = _repo.obtener_semestre(num, plan.id_plan)
                id_t  = _repo.obtener_id_tipo(tipo)
                # Crear un detalle_semestre por cada LIES
                for id_lies in ids_lies:
                    id_d = _repo.crear_detalle(id_s, id_t, id_lies)
                    _repo.guardar_materia(nom, tipo, id_d, plan.id_plan)

            _mostrar_exito(f"Plan guardado\nID {plan.id_plan}")
        except Exception as ex:
            import traceback
            # Rollback para limpiar la sesión de BD en estado inválido
            try:
                if _db:
                    _db.rollback()
            except Exception:
                pass
            traceback.print_exc()
            print(f"[ERROR _guardar] {ex}")

    # ── TABLA ────────────────────────────────────────────────────────────────
    def _hdr(label: str, width: int, left_border=False) -> ft.Container:
        return ft.Container(
            width     = width,
            alignment = ft.alignment.center,
            border    = ft.border.only(left=ft.BorderSide(1, BLANCO)) if left_border else None,
            content   = ft.Text(label, color=BLANCO, size=TS, font_family=F_ROBOTO_C),
        )

    btn_agregar = ft.Container(
        width=32, height=26,
        bgcolor=AZUL, border_radius=4,
        alignment=ft.alignment.center,
        on_click=_agregar_fila,
        content=ft.Text("+", color=BLANCO, size=18,
                        weight=ft.FontWeight.BOLD, font_family=F_ROBOTO_C),
    )

    tabla_block = ft.Container(
        width   = W_TABLA,
        content = ft.Column(
            spacing  = 4,
            controls = [
                ft.Row(alignment=ft.MainAxisAlignment.END, controls=[btn_agregar]),
                ft.Container(
                    width  = W_TABLA,
                    border = ft.border.all(1, AZUL),
                    content= ft.Column(
                        spacing  = 0,
                        controls = [
                            ft.Container(
                                height=32, bgcolor=AZUL,
                                content=ft.Row(
                                    spacing=0,
                                    controls=[
                                        _hdr("Nombre",   W_NOMBRE),
                                        _hdr("Tipo",     W_TIPO,     left_border=True),
                                        _hdr("Semestre", W_SEMESTRE, left_border=True),
                                    ],
                                ),
                            ),
                            filas,
                        ],
                    ),
                ),
            ],
        ),
    )

    # ── HEADER ───────────────────────────────────────────────────────────────
    header = ft.Container(
        bgcolor = BLANCO,
        padding = ft.padding.symmetric(horizontal=16, vertical=8),
        border  = ft.border.only(bottom=ft.BorderSide(2, AZUL)),
        content = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=48, height=48,
                    border=ft.border.all(2, AZUL), border_radius=4,
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, color=AZUL, size=26),
                ),
                ft.Text(
                    "Crear plan de estudios",
                    size=24, color=AZUL, font_family=F_ADAMINA,
                    text_align=ft.TextAlign.CENTER, expand=True,
                ),
                ft.Container(
                    width=36, height=36,
                    bgcolor=ROJO, border_radius=4,
                    alignment=ft.alignment.center,
                    on_click=lambda e: page.window.close(),
                    content=ft.Text("X", color=BLANCO, size=TS,
                                    weight=ft.FontWeight.BOLD, font_family=F_ROBOTO_C),
                ),
            ],
        ),
    )

    # ── CUERPO ───────────────────────────────────────────────────────────────
    contenido = ft.Container(
        width   = W_TABLA + 40,
        content = ft.Column(
            spacing=18, expand=True,
            controls=[
                fila_botones,
                ft.Row(
                    spacing=40,
                    controls=[
                        ft.Column(spacing=4, controls=[
                            ft.Text("Nombre del plan:", weight=ft.FontWeight.BOLD,
                                    size=TS, color=NEGRO, font_family=F_ROBOTO_C),
                            f_nombre,
                        ]),
                        ft.Column(spacing=4, controls=[
                            ft.Text("Fecha de inicio", weight=ft.FontWeight.BOLD,
                                    size=TS, color=NEGRO, font_family=F_ROBOTO_C),
                            f_fecha,
                        ]),
                    ],
                ),
                tabla_block,
                ft.Container(expand=True),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    controls=[
                        ft.ElevatedButton(
                            content=ft.Text("Guardar", font_family=F_INTER,
                                            size=TS, weight=ft.FontWeight.W_600, color=BLANCO),
                            width=180, height=44, bgcolor=AZUL,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                            on_click=_guardar,
                        ),
                        ft.ElevatedButton(
                            content=ft.Text("Cancelar", font_family=F_INTER,
                                            size=TS, weight=ft.FontWeight.W_600, color=BLANCO),
                            width=180, height=44, bgcolor=ROJO,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                            on_click=lambda e: page.window.close(),
                        ),
                    ],
                ),
            ],
        ),
    )

    body = ft.Container(
        expand=True,
        padding=ft.padding.symmetric(horizontal=20, vertical=24),
        alignment=ft.alignment.top_center,
        content=contenido,
    )

    return ft.Column(spacing=0, expand=True, controls=[header, body])