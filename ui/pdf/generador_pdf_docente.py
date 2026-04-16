"""
ui/pdf/generador_pdf_docente.py
Genera un PDF de horario semanal de un docente en orientación vertical (carta):
  - Membrete (imagen de fondo a página completa, opcional)
  - Encabezado: Plan de estudios, Semestre, Docente
  - Tabla semanal: Hora | Lunes | Martes | Miércoles | Jueves | Viernes
  - Celdas con color azul claro para materias ocupadas

Los textos se superponen sobre el membrete usando el mismo enfoque
que generador_pdf.py (callback onFirstPage/onLaterPages).
"""

import os
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

    # ── Tabla de horario semanal ──────────────────────────────

    def _tabla_horario(self) -> Table:
        """Construye la tabla Hora | Lunes | … | Viernes."""
        filas = self._resumen.filas

        # Franjas horarias únicas ordenadas
        franjas = sorted(set(
            (f.hora_inicio, f.hora_fin) for f in filas
            if f.hora_inicio and f.hora_fin
        ))

        # Encabezado
        header = [Paragraph("Hora", _STY_HDR)] + [
            Paragraph(d, _STY_HDR) for d in _DIAS
        ]
        data = [header]

        # Mapa: (dia, hora_inicio) → nombre_materia
        mapa: dict[tuple, str] = {}
        for f in filas:
            if f.dia and f.hora_inicio:
                mapa[(f.dia, f.hora_inicio)] = f.nombre_materia

        # Datos para mapeo de colores por celda
        cell_texts: list[list[str]] = []

        for (hi, hf) in franjas:
            hora_txt = f"{hi} - {hf}"
            fila = [Paragraph(hora_txt, _STY_HORA)]
            row_texts: list[str] = []
            for dia in _DIAS:
                materia = mapa.get((dia, hi), "")
                row_texts.append(materia)
                fila.append(Paragraph(materia, _STY_CELL))
            cell_texts.append(row_texts)
            data.append(fila)

        # Si no hay datos
        if len(data) == 1:
            data.append(
                [Paragraph("Sin horarios registrados", _STY_CELL)]
                + [Paragraph("", _STY_CELL)] * len(_DIAS)
            )
            cell_texts.append([""] * len(_DIAS))

        # Anchos de columna
        page_w = letter[0] - 3 * cm
        col_hora = 2.5 * cm
        col_dia = (page_w - col_hora) / len(_DIAS)
        col_widths = [col_hora] + [col_dia] * len(_DIAS)

        tabla = Table(data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0),  _AZUL_HDR),
            ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.5, _NEGRO),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 3),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ]

        # Color azul claro para celdas con materia
        for row_idx, row_texts in enumerate(cell_texts, start=1):
            for col_idx, txt in enumerate(row_texts, start=1):
                if txt:
                    style_cmds.append(
                        ("BACKGROUND", (col_idx, row_idx),
                         (col_idx, row_idx), _AZUL_CELL)
                    )

        tabla.setStyle(TableStyle(style_cmds))
        return tabla
