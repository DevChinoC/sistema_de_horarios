"""
Entidad de dominio: Horario

Representa un bloque horario asignado a una materia/unidad de aprendizaje.
Contiene toda la lógica de negocio relacionada con horarios:
- Validación de datos propios
- Detección de traslapes
- Cálculo de duración

PROHIBIDO: importar Flet aquí.
PROHIBIDO: acceder a base de datos aquí.
"""
from __future__ import annotations

from domain.value_objects.hora import Hora
from domain.value_objects.dia_semana import DiaSemana
from domain.exceptions.horario_exceptions import HorarioInvalidoException


class Horario:
    """Bloque horario asignado a una unidad de aprendizaje.

    Atributos de identidad:
        id_horario: ID en BD (None si aún no persistido).

    Atributos de asignación:
        id_asignacion: FK a la asignación del plan de estudios.
        id_docente: FK al docente asignado.
        id_aula: FK al aula asignada.
        id_periodo: FK al periodo académico.
        id_semestre: FK al semestre del plan.
        id_lies: FK a la LIES (Línea de Énfasis) activa.
        id_materia: ID de la materia de tronco (None si es optativa).

    Atributos de horario:
        dia: Día de la semana (value object DiaSemana).
        hora_inicio: Hora de inicio (value object Hora).
        hora_fin: Hora de fin (value object Hora).
    """

    def __init__(
        self,
        dia: str | DiaSemana,
        hora_inicio: str | Hora,
        hora_fin: str | Hora,
        id_asignacion: int,
        id_docente: int,
        id_aula: int,
        id_periodo: int,
        id_semestre: int | None = None,
        id_lies: int | None = None,
        id_materia: int | None = None,
        id_horario: int | None = None,
        total_horas: float | None = None,
    ) -> None:
        # Convertir strings a value objects si es necesario
        self.dia: DiaSemana = (
            dia if isinstance(dia, DiaSemana) else DiaSemana(dia)
        )
        self.hora_inicio: Hora = (
            hora_inicio if isinstance(hora_inicio, Hora) else Hora(hora_inicio)
        )
        self.hora_fin: Hora = (
            hora_fin if isinstance(hora_fin, Hora) else Hora(hora_fin)
        )

        # Identificadores
        self.id_horario = id_horario
        self.id_asignacion = id_asignacion
        self.id_docente = id_docente
        self.id_aula = id_aula
        self.id_periodo = id_periodo
        self.id_semestre = id_semestre
        self.id_lies = id_lies
        self.id_materia = id_materia  # None → optativa
        self._total_horas = total_horas

        # Validar invariantes de la entidad
        self.validar()

    # ── Validación ────────────────────────────────────────────

    def validar(self) -> None:
        """Valida las invariantes del horario.

        Raises:
            HorarioInvalidoException: Si hora_inicio >= hora_fin.
        """
        if self.hora_inicio >= self.hora_fin:
            raise HorarioInvalidoException(
                campo="hora_inicio/hora_fin",
                razon=(
                    f"La hora de inicio ({self.hora_inicio}) debe ser "
                    f"anterior a la hora de fin ({self.hora_fin})."
                ),
            )
        if self.id_asignacion <= 0:
            raise HorarioInvalidoException(
                campo="id_asignacion",
                razon="El ID de asignación debe ser mayor a 0.",
            )

    # ── Lógica de negocio ─────────────────────────────────────

    def traslapa(self, otro: "Horario") -> bool:
        """Determina si este horario se traslapa con otro.

        Dos horarios se traslapan si:
        - Son el mismo día, Y
        - Sus rangos horarios se solapan (inicio de uno < fin del otro Y viceversa).

        No hay traslape si los horarios son en días distintos o si uno
        termina exactamente cuando el otro empieza.

        Args:
            otro: Otro objeto Horario a comparar.

        Returns:
            True si hay traslape, False si no.
        """
        if self.dia != otro.dia:
            return False
        return self.hora_inicio < otro.hora_fin and self.hora_fin > otro.hora_inicio

    def calcular_duracion(self) -> float:
        """Calcula la duración en horas decimales.

        Returns:
            Duración en horas (ej: 1.5 para 90 minutos).
        """
        inicio_min = self.hora_inicio.en_minutos()
        fin_min = self.hora_fin.en_minutos()
        return max(0.0, (fin_min - inicio_min) / 60.0)

    def calcular_duracion_enteros(self) -> int:
        """Calcula la duración en horas enteras (truncado)."""
        return int(self.calcular_duracion())

    def es_tronco_comun(self) -> bool:
        """Retorna True si esta materia pertenece al tronco común.

        Una materia es de tronco común si tiene id_materia asignado.
        Las optativas tienen id_materia == None.
        """
        return self.id_materia is not None

    def mismo_rango_que(self, otro: "Horario") -> bool:
        """Verifica si este horario tiene exactamente el mismo día y rango que otro."""
        return (
            self.dia == otro.dia
            and self.hora_inicio == otro.hora_inicio
            and self.hora_fin == otro.hora_fin
        )

    # ── Representación ────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"Horario(dia='{self.dia}', "
            f"inicio='{self.hora_inicio}', fin='{self.hora_fin}', "
            f"id_asig={self.id_asignacion})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Horario):
            return False
        return (
            self.id_horario is not None
            and self.id_horario == other.id_horario
        )

    def __hash__(self) -> int:
        if self.id_horario is not None:
            return hash(self.id_horario)
        return hash((self.dia, self.hora_inicio, self.hora_fin, self.id_asignacion))
