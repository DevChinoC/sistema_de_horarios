"""
ui/pdf/generador_pdf.py
Genera el PDF de horario en orientación vertical (carta / letter):
  - Membrete (imagen de fondo a página completa, opcional)
  - Encabezado: Plan de estudios + LIES
  - Tabla de horario semanal (Hora | Lunes … Sábado) con colores pastel
  - Tabla resumen (Clave | Docente | Unidad | Horas | Semestre | Aula)

Los textos de las celdas se envuelven automáticamente mediante Paragraph
para evitar desbordamientos en orientación vertical.
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

    # ── Tabla horario semanal ─────────────────────────────────

    def _tabla_horario_semanal(self) -> Table:
        """Construye la tabla Hora | Lunes | Martes … | Sábado.

        Usa Paragraph en cada celda para que el texto se ajuste
        automáticamente al ancho de columna sin desbordarse.
        """

        # Recopilar franjas horarias únicas ordenadas
        franjas = sorted(set(
            (h.hora_inicio, h.hora_fin)
            for h in self._horarios
            if h.hora_inicio and h.hora_fin
        ))

        # Encabezado (Paragraph para wrapping)
        header = [Paragraph("Hora", _STY_HDR)] + [
            Paragraph(d, _STY_HDR) for d in _DIAS
        ]
        data = [header]

        # Mapa rápido: (dia, hora_inicio) → DTO
        mapa: dict[tuple, HorarioRegistradoDTO] = {}
        for h in self._horarios:
            if h.dia and h.hora_inicio:
                mapa[(h.dia, h.hora_inicio)] = h

        # Textos originales para color mapping
        cell_texts: list[list[str]] = []

        for (hi, hf) in franjas:
            fila = [Paragraph(f"{hi[:5]}-{hf[:5]}", _STY_HORA)]
            row_texts: list[str] = []
            for dia in _DIAS:
                h = mapa.get((dia, hi))
                txt = h.unidad if h else ""
                row_texts.append(txt)
                fila.append(Paragraph(txt, _STY_CELL))
            cell_texts.append(row_texts)
            data.append(fila)

        # Si no hay datos de horario
        if len(data) == 1:
            data.append(
                [Paragraph("Sin horarios registrados", _STY_CELL)]
                + [Paragraph("", _STY_CELL)] * 6
            )
            cell_texts.append([""] * 6)

        # Anchos adaptados a portrait (letter vertical)
        page_w = letter[0] - 3 * cm
        col_hora = 2.0 * cm
        col_dia  = (page_w - col_hora) / len(_DIAS)
        col_widths = [col_hora] + [col_dia] * len(_DIAS)

        tabla = Table(data, colWidths=col_widths, repeatRows=1)

        style_cmds = [
            ("BACKGROUND",    (0, 0), (-1, 0),  _AZUL_HDR),
            ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",          (0, 0), (-1, -1), 0.5, _GRIS_BORDE),
            ("TOPPADDING",    (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ]

        # Colores pastel por celda según materia
        for row_idx, row_texts in enumerate(cell_texts, start=1):
            for col_idx, txt in enumerate(row_texts, start=1):
                if txt and txt in self._color_map:
                    style_cmds.append(
                        ("BACKGROUND", (col_idx, row_idx),
                         (col_idx, row_idx), self._color_map[txt])
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

        # Agrupar por unidad para no duplicar filas iguales
        vistos: set[str] = set()
        unidades_por_fila: list[str] = []

        for h in self._horarios:
            key = f"{h.unidad}|{h.docente}"
            if key in vistos:
                continue
            vistos.add(key)
            sem = (str(h.numero_semestre)
                   if h.numero_semestre > 0 else "Optativa")
            unidades_por_fila.append(h.unidad)
            data.append([
                Paragraph(h.clave, _STY_CELL),
                Paragraph(h.docente, _STY_CELL),
                Paragraph(h.unidad, _STY_CELL),
                Paragraph(str(h.total_horas), _STY_CELL),
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
