"""
Excepciones de dominio para el sistema de horarios.

Estas excepciones representan violaciones de reglas de negocio.
Son lanzadas por entidades, validadores y casos de uso.
Los controllers las capturan y las convierten en mensajes para la UI.

PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations


class HorarioConflictException(Exception):
    """Se lanza cuando hay un traslape o conflicto entre horarios.

    Ejemplos:
    - Dos materias de tronco en el mismo rango horario del mismo semestre.
    - Una optativa que colisiona con tronco común.
    - Dos optativas en el mismo horario dentro de la misma LIES.
    - Materia de tronco asignada con diferente aula/docente en otra LIES.
    """

    def __init__(
        self,
        mensaje: str,
        conflictos: list[dict] | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        # Lista opcional de conflictos detallados para mostrar al usuario
        # Cada item: {"dia": str, "hora_inicio": str, "hora_fin": str, ...}
        self.conflictos: list[dict] = conflictos or []

    def __str__(self) -> str:
        return self.mensaje


class HorarioInvalidoException(Exception):
    """Se lanza cuando los datos de un horario no son válidos.

    Ejemplos:
    - Hora de inicio >= hora de fin.
    - Día de semana no reconocido.
    - Formato de hora incorrecto.
    """

    def __init__(self, campo: str, razon: str) -> None:
        mensaje = f"Campo '{campo}' inválido: {razon}"
        super().__init__(mensaje)
        self.campo = campo
        self.razon = razon

    def __str__(self) -> str:
        return f"Campo '{self.campo}' inválido: {self.razon}"


class DocenteNoEncontradoException(Exception):
    """Se lanza cuando no se encuentra un docente por ID."""

    def __init__(self, id_docente: int) -> None:
        super().__init__(f"Docente con ID {id_docente} no encontrado.")
        self.id_docente = id_docente


class AulaNoDisponibleException(Exception):
    """Se lanza cuando un aula no está disponible en el horario solicitado."""

    def __init__(self, id_aula: int, dia: str, hora_inicio: str, hora_fin: str) -> None:
        super().__init__(
            f"El aula {id_aula} no está disponible el {dia} "
            f"de {hora_inicio} a {hora_fin}."
        )
        self.id_aula = id_aula
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin


class PeriodoInvalidoException(Exception):
    """Se lanza cuando el nombre del periodo está vacío o tiene formato inválido."""

    def __init__(self, nombre: str, razon: str = "") -> None:
        msg = f"Periodo '{nombre}' inválido"
        if razon:
            msg += f": {razon}"
        super().__init__(msg)
        self.nombre = nombre
        self.razon = razon
