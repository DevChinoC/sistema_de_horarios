"""
Mappers de Horario.

Convierte entre DTOs, dicts y estructuras de datos para UI.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a BD aquí.
PROHIBIDO: lógica de negocio aquí.
"""
from __future__ import annotations

from datetime import datetime

from application.dto.horario_dto import FilaHorarioDTO, HorarioRegistradoDTO


class HorarioMapper:
    """Convierte datos de horario entre capas."""

    # ── DTO de fila → dict para tabla UI ──────────────────────

    @staticmethod
    def registro_a_dict(registro: HorarioRegistradoDTO) -> dict:
        """Convierte un HorarioRegistradoDTO a dict plano para la UI."""
        return {
            "id_horario":  registro.id_horario,
            "semestre":    registro.semestre,
            "unidad":      registro.unidad,
            "docente":     registro.docente,
            "total_horas": str(registro.total_horas),
            "aulas":       registro.aulas,
            "periodo":     registro.periodo,
            "dia":         registro.dia,
            "hora_inicio": registro.hora_inicio,
            "hora_fin":    registro.hora_fin,
        }

    @staticmethod
    def registros_a_dicts(registros: list[HorarioRegistradoDTO]) -> list[dict]:
        """Convierte lista de registros a lista de dicts para la UI."""
        return [HorarioMapper.registro_a_dict(r) for r in registros]

    # ── Filas raw (widget) → FilaHorarioDTO ───────────────────

    @staticmethod
    def fila_raw_a_dto(fila_raw: dict) -> FilaHorarioDTO | None:
        """Convierte un dict {dia, hora_inicio, hora_fin} a FilaHorarioDTO.

        Retorna None si la fila está incompleta.
        Calcula delta automáticamente.
        """
        dia = (fila_raw.get("dia") or "").strip()
        if not dia:
            return None

        hora_inicio = (fila_raw.get("hora_inicio") or "").strip()
        hora_fin    = (fila_raw.get("hora_fin") or "").strip()

        try:
            t0 = datetime.strptime(hora_inicio, "%H:%M")
            t1 = datetime.strptime(hora_fin, "%H:%M")
            delta = max(0, (t1 - t0).seconds) // 3600
        except ValueError:
            return None  # formato inválido — el caller mostrará el error

        return FilaHorarioDTO(
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            delta=delta,
        )

    @staticmethod
    def filas_raw_a_dtos(filas_raw: list[dict]) -> tuple[list[FilaHorarioDTO], str | None]:
        """Convierte lista de filas raw a FilaHorarioDTOs.

        Returns:
            (filas_validas, error_msg)
            Si error_msg no es None, hay al menos una fila con formato inválido.
        """
        resultado: list[FilaHorarioDTO] = []
        for raw in filas_raw:
            dto = HorarioMapper.fila_raw_a_dto(raw)
            if dto is None and (raw.get("dia") or "").strip():
                # Hay día pero el formato de hora es inválido
                hi = raw.get("hora_inicio", "")
                hf = raw.get("hora_fin", "")
                return [], f"Formato de hora inválido: {hi} – {hf}"
            if dto is not None:
                resultado.append(dto)

        if not resultado:
            return [], "Completa al menos un horario (día + horas)."

        return resultado, None

    # ── Nombre de semestre ────────────────────────────────────

    @staticmethod
    def id_sem_a_nombre(id_sem_str: str, semestres: list) -> str:
        """Retorna 'Semestre N' dado el id como string y lista de SemestreDTO."""
        return next(
            (f"Semestre {s.numero}" for s in semestres if str(s.id) == id_sem_str),
            "",
        )
