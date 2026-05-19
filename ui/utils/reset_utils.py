"""
ui/utils/reset_utils.py
Helper centralizado para restauración visual de controles Flet.

Flet tiene un bug conocido: dropdown.value = None NO limpia el texto
renderizado visualmente. La solución es destruir el Dropdown viejo y
crear uno nuevo con las mismas propiedades de estilo, swappeándolo
en el parent.controls.
"""

import flet as ft


def reset_dropdown(
    dropdown: ft.Dropdown,
    *,
    options: list[ft.dropdown.Option] | None = None,
    disabled: bool = True,
    value: str | None = None,
) -> ft.Dropdown:
    """Reinicia un Dropdown destruyéndolo y recreándolo.

    Flet NO soporta ``dropdown.value = None`` para volver al hint_text.
    Este helper crea un Dropdown nuevo con las mismas propiedades
    visuales y lo reemplaza en el árbol de controles del padre.

    **IMPORTANTE**: Retorna el nuevo Dropdown. El caller DEBE guardar
    la referencia::

        self._dd_grado = reset_dropdown(self._dd_grado, ...)

    Parámetros:
        dropdown : control ft.Dropdown a reemplazar
        options  : nuevas opciones (vacía por defecto)
        disabled : si queda deshabilitado (True por defecto)
        value    : valor seleccionado (None por defecto)

    Returns:
        El nuevo ft.Dropdown ya insertado en el árbol.
    """
    new_dd = ft.Dropdown(
        hint_text=dropdown.hint_text,
        options=options if options is not None else [],
        disabled=disabled,
        value=value,
        on_change=dropdown.on_change,
        menu_height=dropdown.menu_height,
        # Copiar propiedades visuales
        border_color=dropdown.border_color,
        focused_border_color=dropdown.focused_border_color,
        bgcolor=dropdown.bgcolor,
        fill_color=dropdown.fill_color,
        color=dropdown.color,
        text_size=dropdown.text_size,
        width=dropdown.width,
        content_padding=dropdown.content_padding,
        text_style=dropdown.text_style,
        hint_style=dropdown.hint_style,
    )

    # Reemplazar en el padre
    parent = dropdown.parent
    if parent is not None and hasattr(parent, 'controls'):
        idx = None
        for i, ctrl in enumerate(parent.controls):
            if ctrl is dropdown:
                idx = i
                break
        if idx is not None:
            parent.controls[idx] = new_dd

    return new_dd

