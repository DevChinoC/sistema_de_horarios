"""
Value Object: DiaSemana

Representa un día de la semana válido.
Elimina strings mágicos dispersos por el sistema.

PROHIBIDO: importar Flet aquí.
"""
from __future__ import annotations


class DiaSemana:
    """Día de la semana con validación automática.

    Valores aceptados (case-insensitive, normalizado con capitalize):
        Lunes, Martes, Miércoles, Jueves, Viernes, Sábado, Domingo

    Ejemplos:
        >>> DiaSemana("Lunes")
        >>> DiaSemana("lunes")   # normalizado a "Lunes"
        >>> DiaSemana("Marte")   # lanza ValueError
    """

    # Orden canónico para ordenar horarios por día
    VALORES: list[str] = [
        "Lunes", "Martes", "Miércoles", "Jueves",
        "Viernes", "Sábado", "Domingo",
    ]

    _ALIAS: dict[str, str] = {
        "miercoles": "Miércoles",
        "miércoles": "Miércoles",
        "sabado":    "Sábado",
        "sábado":    "Sábado",
    }

    def __init__(self, valor: str) -> None:
        """
        Args:
            valor: Nombre del día. Case-insensitive.

        Raises:
            ValueError: Si el valor no corresponde a un día válido.
        """
        if not isinstance(valor, str):
            raise ValueError(
                f"DiaSemana debe ser una cadena, recibido: {type(valor)}"
            )
        self._valor: str = self._normalizar(valor.strip())
        self._validar()

    def _normalizar(self, raw: str) -> str:
        """Normaliza el valor: primero busca alias, luego capitalize."""
        lower = raw.lower()
        if lower in self._ALIAS:
            return self._ALIAS[lower]
        return raw.capitalize()

    def _validar(self) -> None:
        if self._valor not in self.VALORES:
            raise ValueError(
                f"Día '{self._valor}' no es válido. "
                f"Valores aceptados: {', '.join(self.VALORES)}"
            )

    # ── API pública ───────────────────────────────────────────

    @property
    def valor(self) -> str:
        """Nombre del día normalizado (ej: 'Lunes', 'Miércoles')."""
        return self._valor

    @property
    def indice(self) -> int:
        """Posición en la semana (0=Lunes … 6=Domingo)."""
        return self.VALORES.index(self._valor)

    def es_fin_de_semana(self) -> bool:
        return self._valor in ("Sábado", "Domingo")

    # ── Comparaciones ─────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DiaSemana):
            return self._valor == other._valor
        if isinstance(other, str):
            return self._valor == other
        return False

    def __hash__(self) -> int:
        return hash(self._valor)

    def __lt__(self, other: "DiaSemana") -> bool:
        return self.indice < other.indice

    def __repr__(self) -> str:
        return f"DiaSemana('{self._valor}')"

    def __str__(self) -> str:
        return self._valor
