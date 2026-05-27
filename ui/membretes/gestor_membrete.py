"""gestor_membrete.py
Responsabilidad única: copiar/eliminar/resolver la ruta del membrete
de un plan dentro de un directorio persistente de datos de usuario.

El directorio de almacenamiento es:
  Windows : C:/Users/<usuario>/AppData/Local/SistemaHorarios/membretes/
  macOS   : ~/Library/Application Support/SistemaHorarios/membretes/
  Linux   : ~/.local/share/SistemaHorarios/membretes/

Esto garantiza que funciona tanto en desarrollo como en el ejecutable
empaquetado, donde ui/membretes/ puede ser de solo lectura.
"""

import os
import shutil
import platform
from pathlib import Path


def _directorio_app() -> Path:
    """Devuelve el directorio de datos persistentes de la aplicación."""
    sistema = platform.system()
    if sistema == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sistema == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "SistemaHorarios" / "membretes"


class GestorMembrete:
    """Gestiona el almacenamiento de imágenes de membrete por plan.

    Cada plan tiene su propio subdirectorio:
        <directorio_app>/membretes/<id_plan>/membrete.<ext>
    """

    def __init__(self, id_plan: int) -> None:
        if id_plan <= 0:
            raise ValueError(f"id_plan debe ser positivo, recibido: {id_plan}")
        self._id_plan    = id_plan
        self._directorio = _directorio_app() / str(id_plan)

    # ── API pública (sin cambios, compatible con el resto del sistema) ──

    def guardar(self, ruta_origen: str) -> str:
        origen = Path(ruta_origen)
        if not origen.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_origen}")

        ext = origen.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg"}:
            raise ValueError(f"Extensión no permitida: {ext}")

        self._asegurar_directorio()
        destino = self._directorio / f"membrete{ext}"
        self._limpiar_anteriores(ext)
        shutil.copy2(str(origen), str(destino))
        return str(destino)

    def obtener_ruta(self) -> str | None:
        if not self._directorio.is_dir():
            return None
        for ext in (".png", ".jpg", ".jpeg"):
            candidato = self._directorio / f"membrete{ext}"
            if candidato.is_file():
                return str(candidato)
        return None

    def eliminar(self) -> None:
        ruta = self.obtener_ruta()
        if ruta:
            Path(ruta).unlink(missing_ok=True)

    # ── Privados ────────────────────────────────────────────────

    def _asegurar_directorio(self) -> None:
        self._directorio.mkdir(parents=True, exist_ok=True)

    def _limpiar_anteriores(self, nueva_ext: str) -> None:
        for ext in (".png", ".jpg", ".jpeg"):
            if ext == nueva_ext:
                continue
            (self._directorio / f"membrete{ext}").unlink(missing_ok=True)


def resolver_membrete_plan(id_plan: int) -> str | None:
    return GestorMembrete(id_plan).obtener_ruta()