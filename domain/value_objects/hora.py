"""
Value Object: Hora

Representa una hora en formato HH:MM (24h).
Garantiza que el valor sea siempre válido mediante validación en construcción.

PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations

from datetime import time


class Hora:
    """Hora inmutable en formato HH:MM (24 horas).

    Ejemplos:
        >>> Hora("07:00")
        >>> Hora("23:59")
        >>> Hora("25:00")  # lanza ValueError
    """

    def __init__(self, valor: str) -> None:
        """
        Args:
            valor: Cadena en formato "HH:MM" (24h). Ej: "07:30", "13:00".

        Raises:
            ValueError: Si el formato es inválido o la hora está fuera de rango.
        """
        if not isinstance(valor, str):
            raise ValueError(f"Hora debe ser una cadena, recibido: {type(valor)}")
        self._valor = valor.strip()
        self._time: time = self._validar()

    def _validar(self) -> time:
        """Valida el formato y retorna el objeto time interno."""
        partes = self._valor.split(":")
        if len(partes) != 2:
            raise ValueError(
                f"Formato de hora inválido '{self._valor}'. "
                f"Se espera 'HH:MM' (ej: '07:30')."
            )
        try:
            horas = int(partes[0])
            minutos = int(partes[1])
        except ValueError:
            raise ValueError(
                f"La hora '{self._valor}' contiene caracteres no numéricos."
            )
        if not (0 <= horas <= 23):
            raise ValueError(
                f"Hora '{horas}' fuera de rango (debe ser 0–23)."
            )
        if not (0 <= minutos <= 59):
            raise ValueError(
                f"Minutos '{minutos}' fuera de rango (debe ser 0–59)."
            )
        return time(horas, minutos)

    # ── API pública ───────────────────────────────────────────

    @property
    def valor(self) -> str:
        """Representación en formato HH:MM."""
        return self._valor

    def to_time(self) -> time:
        """Retorna el objeto datetime.time equivalente."""
        return self._time

    def en_minutos(self) -> int:
        """Total de minutos desde medianoche (para comparaciones rápidas)."""
        return self._time.hour * 60 + self._time.minute

    # ── Comparaciones ─────────────────────────────────────────

    def __lt__(self, other: "Hora") -> bool:
        self._verificar_tipo(other)
        return self._time < other._time

    def __le__(self, other: "Hora") -> bool:
        self._verificar_tipo(other)
        return self._time <= other._time

    def __gt__(self, other: "Hora") -> bool:
        self._verificar_tipo(other)
        return self._time > other._time

    def __ge__(self, other: "Hora") -> bool:
        self._verificar_tipo(other)
        return self._time >= other._time

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hora):
            return False
        return self._time == other._time

    def __hash__(self) -> int:
        return hash(self._time)

    def __repr__(self) -> str:
        return f"Hora('{self._valor}')"

    def __str__(self) -> str:
        return self._valor

    # ── Helper ────────────────────────────────────────────────

    @staticmethod
    def _verificar_tipo(other: object) -> None:
        if not isinstance(other, Hora):
            raise TypeError(
                f"No se puede comparar Hora con {type(other).__name__}"
            )
