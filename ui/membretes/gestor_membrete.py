"""gestor_membrete.py
Responsabilidad única: copiar/eliminar/resolver la ruta del membrete
de un plan dentro de la carpeta ui/membretes/<id_plan>/.

Principios POO aplicados:
  - Encapsulamiento  → toda la lógica de rutas vive aquí.
  - Responsabilidad única → solo gestiona archivos de membretes.
  - Abierto/cerrado  → se puede extender la estrategia de nombrado
                        sin tocar el resto del sistema.
"""

import os
import shutil
from pathlib import Path


class GestorMembrete:
    """Gestiona el almacenamiento local de imágenes de membrete.

    Cada plan tiene su propio subdirectorio:
        ui/membretes/<id_plan>/membrete.<ext>

    La ruta base se calcula a partir de la ubicación de este mismo
    módulo, por lo que es independiente del directorio de trabajo.
    """

    # Carpeta raíz de membretes, relativa a este archivo
    _CARPETA_RAIZ: Path = Path(__file__).parent

    # ── Constructor ──────────────────────────────────────────────

    def __init__(self, id_plan: int) -> None:
        if id_plan <= 0:
            raise ValueError(f"id_plan debe ser positivo, recibido: {id_plan}")
        self._id_plan   = id_plan
        self._directorio = self._CARPETA_RAIZ / str(id_plan)

    # ── API pública ──────────────────────────────────────────────

    def guardar(self, ruta_origen: str) -> str:
        """Copia la imagen al directorio del plan y devuelve la ruta destino.

        Parámetros
        ----------
        ruta_origen : ruta absoluta del archivo seleccionado por el usuario.

        Retorna
        -------
        Ruta absoluta del archivo copiado dentro del proyecto.

        Excepciones
        -----------
        FileNotFoundError  si ruta_origen no existe.
        ValueError         si la extensión no está permitida.
        """
        origen = Path(ruta_origen)
        if not origen.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_origen}")

        ext = origen.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg"}:
            raise ValueError(f"Extensión no permitida: {ext}")

        self._asegurar_directorio()
        destino = self._directorio / f"membrete{ext}"

        # Si ya existe un membrete previo con distinta extensión, se elimina
        self._limpiar_anteriores(ext)

        shutil.copy2(str(origen), str(destino))
        return str(destino)

    def obtener_ruta(self) -> str | None:
        """Devuelve la ruta del membrete guardado o None si no existe."""
        if not self._directorio.is_dir():
            return None
        for ext in (".png", ".jpg", ".jpeg"):
            candidato = self._directorio / f"membrete{ext}"
            if candidato.is_file():
                return str(candidato)
        return None

    def eliminar(self) -> None:
        """Borra el membrete (si existe) del directorio del plan."""
        ruta = self.obtener_ruta()
        if ruta:
            Path(ruta).unlink(missing_ok=True)

    # ── Métodos privados ─────────────────────────────────────────

    def _asegurar_directorio(self) -> None:
        self._directorio.mkdir(parents=True, exist_ok=True)

    def _limpiar_anteriores(self, nueva_ext: str) -> None:
        """Elimina membretes previos si tienen una extensión diferente."""
        for ext in (".png", ".jpg", ".jpeg"):
            if ext == nueva_ext:
                continue
            previo = self._directorio / f"membrete{ext}"
            previo.unlink(missing_ok=True)


# ── Función de conveniencia (no rompe POO, es un factory helper) ───

def resolver_membrete_plan(id_plan: int) -> str | None:
    """Atajo para obtener la ruta del membrete de un plan sin instanciar
    directamente GestorMembrete desde capas superiores."""
    return GestorMembrete(id_plan).obtener_ruta()
