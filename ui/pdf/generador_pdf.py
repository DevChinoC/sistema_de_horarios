"""
ui/pdf/generador_pdf.py
Genera el PDF de horario en orientación vertical (carta / letter):
  - Membrete (imagen de fondo a página completa, opcional)
  - Encabezado: Plan de estudios + LIES
  - Tabla de horario semanal (Hora | Lunes … Sábado) con colores pastel
    Construida con TIMELINE DINÁMICO — cada fila es un slot temporal,
    NO una materia. Las materias ocupan spans verticales proporcionales.
  - Tabla resumen (Clave | Docente | Unidad | Horas | Semestre | Aula)

Los textos de las celdas se envuelven automáticamente mediante Paragraph
para evitar desbordamientos en orientación vertical.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from application.dto.horario_dto import HorarioRegistradoDTO


# ─────────────────────────────────────────────────────────────
# Paleta de colores pastel para las materias
# ─────────────────────────────────────────────────────────────
_PASTEL = [
    colors.Color(0.71, 0.85, 0.95),   # azul cielo
    colors.Color(0.72, 0.92, 0.74),   # verde menta
    colors.Color(1.00, 0.93, 0.70),   # amarillo suave
    colors.Color(0.96, 0.75, 0.75),   # rosa salmón
    colors.Color(0.80, 0.72, 0.94),   # lavanda
    colors.Color(0.75, 0.93, 0.93),   # aguamarina
    colors.Color(0.98, 0.80, 0.65),   # durazno
    colors.Color(0.85, 0.94, 0.70),   # lima
]

_AZUL_HDR   = colors.Color(0.20, 0.40, 0.75)   # azul encabezado tabla
_BLANCO     = colors.white
_GRIS_BORDE = colors.Color(0.75, 0.75, 0.75)
_NEGRO      = colors.black

_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]


# ─────────────────────────────────────────────────────────────
# Estilos de celda — Paragraph para auto-wrap de texto
# ─────────────────────────────────────────────────────────────
_STY_HDR = ParagraphStyle(
    "cell_hdr", fontSize=8, leading=10, alignment=TA_CENTER,
    textColor=_BLANCO, fontName="Helvetica-Bold",
)
_STY_HORA = ParagraphStyle(
    "cell_hora", fontSize=7, leading=9, alignment=TA_CENTER,
    textColor=_NEGRO, fontName="Helvetica-Bold",
)
_STY_CELL = ParagraphStyle(
    "cell_txt", fontSize=7, leading=9, alignment=TA_CENTER,
    textColor=_NEGRO,
)


# ─────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────
class GeneradorPDF:
    """Genera el PDF de horario escolar en orientación vertical (portrait).

    Usa un motor de timeline dinámico: las filas de la tabla representan
    slots temporales uniformes (30 o 60 min), NO materias individuales.
    Las materias se insertan como spans verticales proporcionales.

    Parámetros
    ----------
    horarios       : lista de HorarioRegistradoDTO con dia/hora_inicio/hora_fin
    nombre_plan    : texto para el encabezado
    nombre_lies    : LIES activa seleccionada
    ruta_membrete  : path al archivo de imagen del membrete (puede ser None)
    ruta_salida    : path completo del PDF a generar
    """

    def __init__(
        self,
        horarios: list[HorarioRegistradoDTO],
        nombre_plan: str,
        nombre_lies: str,
        ruta_membrete: Optional[str],
        ruta_salida: str,
        nombre_semestre: str = "",
    ) -> None:
        self._horarios      = horarios
        self._nombre_plan   = nombre_plan
        self._nombre_lies   = nombre_lies
        self._nombre_sem    = nombre_semestre
        self._ruta_membrete = ruta_membrete
        self._ruta_salida   = ruta_salida

        # Asignar color pastel a cada unidad única
        unidades_unicas = list(dict.fromkeys(h.unidad for h in horarios))
        self._color_map: dict[str, colors.Color] = {
            u: _PASTEL[i % len(_PASTEL)]
            for i, u in enumerate(unidades_unicas)
        }

    def generar(self) -> str:
        """Genera el PDF y retorna la ruta del archivo creado."""
        tiene_membrete = bool(
            self._ruta_membrete and os.path.exists(self._ruta_membrete)
        )
        # topMargin alto para no tapar el encabezado del membrete
        top = 4.5 * cm if tiene_membrete else 1.2 * cm

        doc = SimpleDocTemplate(
            self._ruta_salida,
            pagesize=letter,                       # ← vertical (portrait)
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=top,
            bottomMargin=1.5 * cm,
        )

        story: list = []
        story.append(Spacer(1, 0.2 * cm))

        # ── Encabezado de texto ──────────────────────────────────
        estilo_enc = ParagraphStyle(
            "enc", fontSize=11, alignment=TA_LEFT,
            textColor=_NEGRO, leading=16,
            fontName="Helvetica-Bold",
        )
        story.append(Paragraph(
            f"Plan de estudios: <b>{self._nombre_plan}</b>", estilo_enc))
        # Solo mostrar LIES si tiene valor (MIIDT); omitir para DIIDT/otros
        if self._nombre_lies:
            story.append(Paragraph(
                f"Lies: <b>{self._nombre_lies}</b>", estilo_enc))
        if self._nombre_sem:
            story.append(Paragraph(
                f"Semestre: <b>{self._nombre_sem}</b>", estilo_enc))
        story.append(Spacer(1, 0.4 * cm))

        # ── Tabla de horario semanal ─────────────────────────────
        story.append(self._tabla_horario_semanal())
        story.append(Spacer(1, 0.6 * cm))

        # ── Tabla resumen ────────────────────────────────────────
        story.append(self._tabla_resumen())

        # Callback para dibujar el membrete como fondo de página
        if tiene_membrete:
            doc.build(story,
                      onFirstPage=self._dibujar_membrete,
                      onLaterPages=self._dibujar_membrete)
        else:
            doc.build(story)
        return self._ruta_salida

    # ── Membrete (fondo de página completa) ───────────────────

    def _dibujar_membrete(self, canvas, doc):
        """Dibuja el membrete ajustado a la hoja carta vertical."""
        canvas.saveState()
        page_w, page_h = letter
        canvas.drawImage(
            self._ruta_membrete,
            0, 0,
            width=page_w,
            height=page_h,
            preserveAspectRatio=True,
            anchor="n",
            mask="auto",
        )
        canvas.restoreState()

    # ══════════════════════════════════════════════════════════
    # Motor de Timeline Dinámico
    # ══════════════════════════════════════════════════════════

    @staticmethod
    def _parse_time(t: str) -> datetime:
        """Convierte 'HH:MM' a datetime para aritmética."""
        return datetime.strptime(t[:5], "%H:%M")

    def _detectar_resolucion_minima(self) -> int:
        """Detecta si el horario necesita slots de 30 o 60 minutos.

        Si alguna hora_inicio o hora_fin tiene minutos != 0 y != 30,
        usa 30 min. Si todo es :00 exacto, usa 60 min.
        Si existe :30, usa 30 min.
        """
        for h in self._horarios:
            for t in (h.hora_inicio, h.hora_fin):
                if not t:
                    continue
                mins = self._parse_time(t).minute
                if mins not in (0, 30, 60):
                    return 30
                if mins == 30:
                    return 30
        return 60

    def _obtener_rango_horario(self) -> tuple[datetime, datetime]:
        """Retorna (hora_min, hora_max) del rango de todos los horarios."""
        horas_inicio = []
        horas_fin = []
        for h in self._horarios:
            if h.hora_inicio and h.hora_fin:
                horas_inicio.append(self._parse_time(h.hora_inicio))
                horas_fin.append(self._parse_time(h.hora_fin))
        if not horas_inicio:
            # Fallback: 08:00 - 15:00
            return self._parse_time("08:00"), self._parse_time("15:00")
        return min(horas_inicio), max(horas_fin)

    def _generar_slots(self) -> list[tuple[str, str]]:
        """Genera la lista de slots temporales uniformes.

        Retorna [(inicio, fin), ...] como strings 'HH:MM'.
        Ejemplo con resolución 60: [('08:00','09:00'), ('09:00','10:00'), ...]
        """
        resolucion = self._detectar_resolucion_minima()
        hora_min, hora_max = self._obtener_rango_horario()
        delta = timedelta(minutes=resolucion)

        slots = []
        current = hora_min
        while current < hora_max:
            next_t = current + delta
            slots.append((current.strftime("%H:%M"), next_t.strftime("%H:%M")))
            current = next_t
        return slots

    def _crear_grid(self, slots: list[tuple[str, str]]) -> dict:
        """Crea un grid vacío: grid[dia][slot_idx] = info de celda.

        Cada celda: {"unidad": "", "color": None, "span_start": False, "skip": False}
        """
        grid = {}
        for dia in _DIAS:
            grid[dia] = {}
            for idx in range(len(slots)):
                grid[dia][idx] = {
                    "unidad": "",
                    "color": None,
                    "span_start": False,
                    "skip": False,  # True si esta celda es parte de un span
                }
        return grid

    def _insertar_materias(self, grid: dict, slots: list[tuple[str, str]]) -> list:
        """Inserta las materias en el grid según su duración real.

        Retorna lista de spans: [(col_idx, row_start, row_end), ...]
        para aplicar SPAN en la tabla de reportlab.
        """
        # Índice rápido de slot_inicio → idx
        slot_map = {s[0]: i for i, s in enumerate(slots)}
        # Índice de fin de slot → idx (para calcular último slot)
        slot_end_map = {s[1]: i for i, s in enumerate(slots)}

        spans = []

        for h in self._horarios:
            if not h.dia or not h.hora_inicio or not h.hora_fin:
                continue
            if h.dia not in grid:
                continue

            hi = h.hora_inicio[:5]
            hf = h.hora_fin[:5]

            # Encontrar el primer slot que empieza a la hora de inicio
            if hi not in slot_map:
                continue
            start_idx = slot_map[hi]

            # Encontrar el último slot que termina a la hora de fin
            if hf not in slot_end_map:
                # Si hora_fin no coincide exactamente, buscar el slot más cercano
                end_idx = start_idx
                for idx, (_, sf) in enumerate(slots):
                    if self._parse_time(sf) <= self._parse_time(hf):
                        end_idx = idx
            else:
                end_idx = slot_end_map[hf]

            dia = h.dia
            col_idx = _DIAS.index(dia) + 1 if dia in _DIAS else None
            if col_idx is None:
                continue

            # Verificar solapamientos — no escribir si ya ocupado
            conflicto = False
            for idx in range(start_idx, end_idx + 1):
                if grid[dia][idx]["skip"] or grid[dia][idx]["unidad"]:
                    conflicto = True
                    break

            if conflicto:
                continue

            # Escribir texto solo en la primera celda
            grid[dia][start_idx]["unidad"] = h.unidad
            grid[dia][start_idx]["color"] = self._color_map.get(h.unidad)
            grid[dia][start_idx]["span_start"] = True

            # Marcar celdas internas como parte del span
            for idx in range(start_idx + 1, end_idx + 1):
                grid[dia][idx]["skip"] = True
                grid[dia][idx]["color"] = self._color_map.get(h.unidad)

            # Registrar span si ocupa más de una celda
            if end_idx > start_idx:
                spans.append((col_idx, start_idx, end_idx))

        return spans

    # ── Tabla horario semanal ─────────────────────────────────

    def _tabla_horario_semanal(self) -> Table:
        """Construye la tabla Hora | Lunes | Martes … | Sábado.

        Motor de timeline dinámico:
        1. Detecta resolución (30/60 min)
        2. Genera slots uniformes
        3. Crea grid temporal
        4. Inserta materias con spans verticales
        5. Construye la tabla con datos y estilos
        """
        slots = self._generar_slots()
        grid = self._crear_grid(slots)
        spans = self._insertar_materias(grid, slots)

        resolucion = self._detectar_resolucion_minima()

        # ── Encabezado ────────────────────────────────────────
        header = [Paragraph("Hora", _STY_HDR)] + [
            Paragraph(d, _STY_HDR) for d in _DIAS
        ]
        data = [header]

        # ── Filas del timeline ────────────────────────────────
        for slot_idx, (si, sf) in enumerate(slots):
            fila = [Paragraph(f"{si}-{sf}", _STY_HORA)]
            for dia in _DIAS:
                celda = grid[dia][slot_idx]
                if celda["skip"]:
                    # Celda parte de un span — vacía (se fusionará)
                    fila.append(Paragraph("", _STY_CELL))
                elif celda["unidad"]:
                    fila.append(Paragraph(celda["unidad"], _STY_CELL))
                else:
                    fila.append(Paragraph("", _STY_CELL))
            data.append(fila)

        # Si no hay datos de horario
        if len(data) == 1:
            data.append(
                [Paragraph("Sin horarios registrados", _STY_CELL)]
                + [Paragraph("", _STY_CELL)] * 6
            )

        # ── Anchos de columna ─────────────────────────────────
        page_w = letter[0] - 3 * cm
        col_hora = 2.0 * cm
        col_dia  = (page_w - col_hora) / len(_DIAS)
        col_widths = [col_hora] + [col_dia] * len(_DIAS)

        # ── Alturas de fila dinámicas ─────────────────────────
        row_h = 18 if resolucion == 30 else 28
        row_heights = [None] + [row_h] * len(slots)  # None = auto para header

        tabla = Table(data, colWidths=col_widths, rowHeights=row_heights,
                      repeatRows=1)

        # ── Estilos base ──────────────────────────────────────
        style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0),  _AZUL_HDR),
            ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.5, _GRIS_BORDE),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ]

        # ── Colores pastel por celda ──────────────────────────
        for slot_idx in range(len(slots)):
            for dia_idx, dia in enumerate(_DIAS):
                col = dia_idx + 1
                row = slot_idx + 1  # +1 por header
                celda = grid[dia][slot_idx]
                if celda["color"]:
                    style_cmds.append(
                        ("BACKGROUND", (col, row), (col, row), celda["color"])
                    )

        # ── Spans verticales (fusión de celdas) ───────────────
        for (col_idx, row_start, row_end) in spans:
            # reportlab SPAN: (col, row_start+1) → (col, row_end+1)
            # +1 porque row 0 es el header
            style_cmds.append(
                ("SPAN", (col_idx, row_start + 1), (col_idx, row_end + 1))
            )

        tabla.setStyle(TableStyle(style_cmds))
        return tabla

    # ── Tabla resumen ─────────────────────────────────────────

    def _tabla_resumen(self) -> Table:
        """Construye la tabla Clave | Docente | Unidad | Horas | Semestre | Aula.

        Usa Paragraph en cada celda para auto-wrap.
        """
        header = [
            Paragraph("Clave", _STY_HDR),
            Paragraph("Docente", _STY_HDR),
            Paragraph("Unidad de aprendizaje", _STY_HDR),
            Paragraph("Horas", _STY_HDR),
            Paragraph("Semestre", _STY_HDR),
            Paragraph("Aula", _STY_HDR),
        ]
        data = [header]

        # ── Paso 1: Acumular horas de sesiones únicas por (unidad, docente) ──
        # Clave de sesión: (unidad, docente, dia, hora_inicio, hora_fin)
        # evita duplicar por LIES/grupos pero suma sesiones distintas.
        sesiones_unicas: dict[tuple, int] = {}
        for h in self._horarios:
            sesion_key = (h.unidad, h.docente, h.dia, h.hora_inicio, h.hora_fin)
            if sesion_key not in sesiones_unicas:
                sesiones_unicas[sesion_key] = h.total_horas

        # ── Paso 2: Consolidar por (unidad, docente) → horas totales ──
        resumen: dict[str, dict] = {}
        for (unidad, docente, dia, hi, hf), horas in sesiones_unicas.items():
            rkey = f"{unidad}|{docente}"
            if rkey not in resumen:
                # Buscar el DTO original para obtener clave/semestre/aulas
                dto_orig = next(
                    h for h in self._horarios
                    if h.unidad == unidad and h.docente == docente
                )
                resumen[rkey] = {
                    "dto": dto_orig,
                    "horas_acum": 0,
                }
            resumen[rkey]["horas_acum"] += horas

        # ── Paso 3: Construir filas del resumen ──
        unidades_por_fila: list[str] = []

        for rkey, info in resumen.items():
            h = info["dto"]
            horas_total = info["horas_acum"]
            sem = (str(h.numero_semestre)
                   if h.numero_semestre > 0 else "Optativa")
            unidades_por_fila.append(h.unidad)
            data.append([
                Paragraph(h.clave, _STY_CELL),
                Paragraph(h.docente, _STY_CELL),
                Paragraph(h.unidad, _STY_CELL),
                Paragraph(str(horas_total), _STY_CELL),
                Paragraph(sem, _STY_CELL),
                Paragraph(h.aulas, _STY_CELL),
            ])

        page_w = letter[0] - 3 * cm
        widths = [
            1.2 * cm,    # Clave
            3.5 * cm,    # Docente
            5.5 * cm,    # Unidad
            1.2 * cm,    # Horas
            1.8 * cm,    # Semestre
            page_w - (1.2 + 3.5 + 5.5 + 1.2 + 1.8) * cm,  # Aula (resto)
        ]

        tabla = Table(data, colWidths=widths, repeatRows=1)

        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0),  _AZUL_HDR),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",       (0, 0), (-1, -1), 0.5, _GRIS_BORDE),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ]

        # Color pastel por fila según unidad
        for row_idx, unidad in enumerate(unidades_por_fila, start=1):
            if unidad in self._color_map:
                style_cmds.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx),
                     self._color_map[unidad])
                )

        tabla.setStyle(TableStyle(style_cmds))
        return tabla
