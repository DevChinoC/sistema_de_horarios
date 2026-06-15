"""
ui/pdf/generador_pdf_docente.py
Genera un PDF de horario semanal de un docente en orientación vertical (carta):
  - Membrete (imagen de fondo a página completa, opcional)
  - Encabezado: Plan de estudios, Semestre, Docente
  - Tabla semanal: Hora | Lunes | Martes | Miércoles | Jueves | Viernes
    Construida con TIMELINE DINÁMICO — cada fila es un slot temporal,
    NO una materia. Las materias ocupan spans verticales proporcionales.
  - Celdas con color azul claro para materias ocupadas

Los textos se superponen sobre el membrete usando el mismo enfoque
que generador_pdf.py (callback onFirstPage/onLaterPages).
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

from application.dto.horario_docente_dto import HorarioDocenteResumenDTO


# ─────────────────────────────────────────────────────────────
# Constantes de estilo
# ─────────────────────────────────────────────────────────────
_AZUL_HDR   = colors.Color(0.24, 0.37, 0.82)   # #3D5FD2
_AZUL_CELL  = colors.Color(0.71, 0.80, 0.97)   # #B5CBF7
_BLANCO     = colors.white
_NEGRO      = colors.black
_GRIS_BORDE = colors.Color(0.75, 0.75, 0.75)

_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]


# ─────────────────────────────────────────────────────────────
# Estilos de celda — Paragraph para auto-wrap de texto
# ─────────────────────────────────────────────────────────────
_STY_HDR = ParagraphStyle(
    "dcell_hdr", fontSize=9, leading=11, alignment=TA_CENTER,
    textColor=_BLANCO, fontName="Helvetica-Bold",
)
_STY_HORA = ParagraphStyle(
    "dcell_hora", fontSize=8, leading=10, alignment=TA_CENTER,
    textColor=_NEGRO, fontName="Helvetica-Bold",
)
_STY_CELL = ParagraphStyle(
    "dcell_txt", fontSize=8, leading=10, alignment=TA_CENTER,
    textColor=_NEGRO,
)


# ─────────────────────────────────────────────────────────────
# Clase principal
# ─────────────────────────────────────────────────────────────
class GeneradorPdfDocente:
    """Genera un PDF con el horario semanal de un docente.

    Usa un motor de timeline dinámico — igual que GeneradorPDF.

    Parámetros
    ----------
    resumen        : HorarioDocenteResumenDTO con datos del docente y filas
    ruta_membrete  : path al archivo de imagen del membrete (puede ser None)
    ruta_salida    : path completo del PDF a generar
    """

    def __init__(
        self,
        resumen: HorarioDocenteResumenDTO,
        ruta_membrete: Optional[str],
        ruta_salida: str,
    ) -> None:
        self._resumen = resumen
        self._ruta_membrete = ruta_membrete
        self._ruta_salida = ruta_salida

    def generar(self) -> str:
        """Genera el PDF y retorna la ruta del archivo creado."""
        tiene_membrete = bool(
            self._ruta_membrete and os.path.exists(self._ruta_membrete)
        )
        # topMargin alto para no tapar el encabezado del membrete
        top = 4.5 * cm if tiene_membrete else 1.2 * cm

        doc = SimpleDocTemplate(
            self._ruta_salida,
            pagesize=letter,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=top,
            bottomMargin=1.5 * cm,
        )

        story: list = []
        story.append(Spacer(1, 0.2 * cm))

        # ── Encabezado de texto ──────────────────────────────
        estilo_enc = ParagraphStyle(
            "denc", fontSize=11, alignment=TA_LEFT,
            textColor=_NEGRO, leading=16,
            fontName="Helvetica-Bold",
        )
        r = self._resumen
        story.append(Paragraph(
            f"Plan de estudios: <b>{r.nombre_plan}</b>", estilo_enc))
        story.append(Paragraph(
            f"Semestre: <b>{r.semestre}</b>", estilo_enc))
        story.append(Paragraph(
            f"Docente: <b>{r.nombre_docente}</b>", estilo_enc))
        story.append(Spacer(1, 0.4 * cm))

        # ── Tabla de horario semanal ─────────────────────────
        story.append(self._tabla_horario())

        # Callback para dibujar el membrete como fondo de página
        draw_bg = self._dibujar_membrete if tiene_membrete else None
        doc.build(story,
                  onFirstPage=draw_bg,
                  onLaterPages=draw_bg)
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
        """Detecta si el horario necesita slots de 30 o 60 minutos."""
        for f in self._resumen.filas:
            for t in (f.hora_inicio, f.hora_fin):
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
        for f in self._resumen.filas:
            if f.hora_inicio and f.hora_fin:
                horas_inicio.append(self._parse_time(f.hora_inicio))
                horas_fin.append(self._parse_time(f.hora_fin))
        if not horas_inicio:
            return self._parse_time("08:00"), self._parse_time("15:00")
        return min(horas_inicio), max(horas_fin)

    def _generar_slots(self) -> list[tuple[str, str]]:
        """Genera la lista de slots temporales uniformes."""
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
        """Crea un grid vacío: grid[dia][slot_idx] = info de celda."""
        grid = {}
        for dia in _DIAS:
            grid[dia] = {}
            for idx in range(len(slots)):
                grid[dia][idx] = {
                    "texto": "",
                    "ocupado": False,
                    "span_start": False,
                    "skip": False,
                }
        return grid

    def _insertar_materias(self, grid: dict, slots: list[tuple[str, str]]) -> list:
        """Inserta las materias en el grid.

        Agrupa por materia → set(LIES) para consolidar etiquetas.
        Retorna lista de spans: [(col_idx, row_start, row_end), ...]
        """
        slot_map = {s[0]: i for i, s in enumerate(slots)}
        slot_end_map = {s[1]: i for i, s in enumerate(slots)}

        # Agrupar: (dia, hora_inicio, hora_fin) → {materia: set(lies)}
        agrupado: dict[tuple, dict[str, set[str]]] = {}
        for f in self._resumen.filas:
            if not f.dia or not f.hora_inicio or not f.hora_fin:
                continue
            key = (f.dia, f.hora_inicio[:5], f.hora_fin[:5])
            materias = agrupado.setdefault(key, {})
            nombre = f.nombre_materia.strip()
            lies_set = materias.setdefault(nombre, set())
            if f.nombre_lies and f.nombre_lies.strip():
                lies_set.add(f.nombre_lies.strip())

        spans = []

        for (dia, hi, hf), materias in agrupado.items():
            if dia not in grid or hi not in slot_map:
                continue

            start_idx = slot_map[hi]
            if hf in slot_end_map:
                end_idx = slot_end_map[hf]
            else:
                end_idx = start_idx

            col_idx = _DIAS.index(dia) + 1 if dia in _DIAS else None
            if col_idx is None:
                continue

            # Verificar solapamientos
            conflicto = False
            for idx in range(start_idx, end_idx + 1):
                if grid[dia][idx]["skip"] or grid[dia][idx]["ocupado"]:
                    conflicto = True
                    break
            if conflicto:
                continue

            # Construir etiqueta consolidada
            etiquetas = []
            for nombre, lies_set in sorted(materias.items()):
                if lies_set:
                    etiquetas.append(
                        f"{nombre}<br/>({', '.join(sorted(lies_set))})")
                else:
                    etiquetas.append(nombre)
            texto_html = "<br/>".join(etiquetas)

            # Escribir en la primera celda
            grid[dia][start_idx]["texto"] = texto_html
            grid[dia][start_idx]["ocupado"] = True
            grid[dia][start_idx]["span_start"] = True

            # Marcar celdas internas
            for idx in range(start_idx + 1, end_idx + 1):
                grid[dia][idx]["skip"] = True
                grid[dia][idx]["ocupado"] = True

            if end_idx > start_idx:
                spans.append((col_idx, start_idx, end_idx))

        return spans

    # ── Tabla de horario semanal ──────────────────────────────

    def _tabla_horario(self) -> Table:
        """Construye la tabla Hora | Lunes | … | Viernes con timeline."""
        filas = self._resumen.filas
        if not filas:
            # Tabla vacía
            header = [Paragraph("Hora", _STY_HDR)] + [
                Paragraph(d, _STY_HDR) for d in _DIAS
            ]
            data = [header]
            data.append(
                [Paragraph("Sin horarios registrados", _STY_CELL)]
                + [Paragraph("", _STY_CELL)] * len(_DIAS)
            )
            page_w = letter[0] - 3 * cm
            col_hora = 2.5 * cm
            col_dia = (page_w - col_hora) / len(_DIAS)
            col_widths = [col_hora] + [col_dia] * len(_DIAS)
            tabla = Table(data, colWidths=col_widths, repeatRows=1)
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _AZUL_HDR),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, _NEGRO),
            ]))
            return tabla

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
            hora_txt = f"{si} - {sf}"
            fila = [Paragraph(hora_txt, _STY_HORA)]
            for dia in _DIAS:
                celda = grid[dia][slot_idx]
                if celda["skip"]:
                    fila.append(Paragraph("", _STY_CELL))
                elif celda["texto"]:
                    fila.append(Paragraph(celda["texto"], _STY_CELL))
                else:
                    fila.append(Paragraph("", _STY_CELL))
            data.append(fila)

        # ── Anchos de columna ─────────────────────────────────
        page_w = letter[0] - 3 * cm
        col_hora = 2.5 * cm
        col_dia = (page_w - col_hora) / len(_DIAS)
        col_widths = [col_hora] + [col_dia] * len(_DIAS)

        # ── Alturas dinámicas ─────────────────────────────────
        row_h = 18 if resolucion == 30 else 28
        row_heights = [None] + [row_h] * len(slots)

        tabla = Table(data, colWidths=col_widths, rowHeights=row_heights,
                      repeatRows=1)

        # ── Estilos ───────────────────────────────────────────
        style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0),  _AZUL_HDR),
            ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.5, _NEGRO),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ]

        # ── Color azul claro para celdas ocupadas ─────────────
        for slot_idx in range(len(slots)):
            for dia_idx, dia in enumerate(_DIAS):
                col = dia_idx + 1
                row = slot_idx + 1
                celda = grid[dia][slot_idx]
                if celda["ocupado"]:
                    style_cmds.append(
                        ("BACKGROUND", (col, row), (col, row), _AZUL_CELL)
                    )

        # ── Spans verticales ──────────────────────────────────
        for (col_idx, row_start, row_end) in spans:
            style_cmds.append(
                ("SPAN", (col_idx, row_start + 1), (col_idx, row_end + 1))
            )

        tabla.setStyle(TableStyle(style_cmds))
        return tabla
