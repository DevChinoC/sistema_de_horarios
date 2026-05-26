"""
Controller: DetallePlanController

Coordina la pantalla de detalle de plan. NO renderiza, NO accede a BD.
Recibe llamadas desde DetallePlanView y delega a los use cases / services.

Responsabilidades:
- Orquestar agregar, editar y eliminar horarios.
- Validar campos del formulario antes de llamar use cases.
- Recopilar y convertir datos de la UI a DTOs.
- Manejar excepciones de dominio y convertirlas a mensajes de texto.
- Preparar datos para la generación de PDF.

PROHIBIDO: importar Flet aquí.
PROHIBIDO: SQL / ORM aquí.
PROHIBIDO: lógica de renderizado aquí.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from application.dto.horario_dto import GuardarHorarioDTO, FilaHorarioDTO, HorarioDetalleDTO
from application.services.horario_service import HorarioService
from application.state.detalle_plan_state import DetallePlanState
from domain.exceptions.horario_exceptions import (
    HorarioConflictException,
    HorarioInvalidoException,
    PeriodoInvalidoException,
)

if TYPE_CHECKING:
    pass

# Clave especial del dropdown "Otro" — igual que en la view
_KEY_NUEVO = "__nuevo__"


class DetallePlanController:
    """Coordina la pantalla DetallePlanView sin renderizar.

    Cada método público corresponde a una acción del usuario.
    Retorna (ok: bool, mensaje: str) para que la View decida
    cómo mostrar el resultado.

    Retorna None cuando no hay datos en vez de lanzar excepción,
    para que la View pueda mostrar el error apropiado.
    """

    def __init__(
        self,
        service: HorarioService,
        state: DetallePlanState,
        id_plan: int,
    ) -> None:
        self._service = service
        self._state = state
        self._id_plan = id_plan

    # ── Validación de formulario ──────────────────────────────

    def validar_formulario(
        self,
        id_asig: str | None,
        id_aula: str | None,
        id_doc: str | None,
        periodo_txt: str,
    ) -> tuple[bool, str]:
        """Valida los campos comunes del formulario.

        Returns:
            (True, "") si todo OK.
            (False, mensaje_error) si hay campo inválido.
        """
        if not id_asig:
            return False, "Selecciona una unidad de aprendizaje."
        if not id_aula or id_aula == _KEY_NUEVO:
            return False, "Selecciona un aula."
        if not id_doc or id_doc == _KEY_NUEVO:
            return False, "Selecciona un docente."
        if not periodo_txt.strip():
            return False, "Escribe el periodo."
        return True, ""

    def recopilar_filas(
        self,
        filas_raw: list[dict],
    ) -> tuple[bool, str, list[FilaHorarioDTO]]:
        """Convierte las filas del formulario a FilaHorarioDTO validados.

        Args:
            filas_raw: Lista de dicts con keys: dia, hora_inicio, hora_fin.

        Returns:
            (True, "", lista_de_filas) si todo OK.
            (False, mensaje_error, []) si hay error de validación.
        """
        filas: list[FilaHorarioDTO] = []
        for raw in filas_raw:
            dia = (raw.get("dia") or "").strip()
            if not dia:
                continue
            hi = raw.get("hora_inicio", "")
            hf = raw.get("hora_fin", "")
            try:
                t0 = datetime.strptime(hi, "%H:%M")
                t1 = datetime.strptime(hf, "%H:%M")
                delta = max(0, (t1 - t0).seconds) // 3600
            except ValueError:
                return False, f"Formato de hora inválido: {hi} – {hf}", []
            filas.append(FilaHorarioDTO(
                dia=dia, hora_inicio=hi, hora_fin=hf, delta=delta,
            ))
        if not filas:
            return False, "Completa al menos un horario (día + horas).", []
        return True, "", filas

    # ── Agregar horario ───────────────────────────────────────

    def agregar_horario(
        self,
        id_asig: str,
        id_aula: str,
        id_doc: str,
        periodo_txt: str,
        filas_validas: list[FilaHorarioDTO],
        id_sem: int | None,
    ) -> tuple[bool, str, list[int]]:
        """Crea uno o más horarios (una fila por registro).

        La validación de conflictos se hace en el backend:
        HorarioService → CrearHorarioUseCase → HorarioValidator → BD real.

        Returns:
            (True, mensaje_ok, ids_creados) si todo OK.
            (False, mensaje_error, []) si hay error.
        """
        # Crear o recuperar periodo
        periodo_dto = self._service.crear_periodo(periodo_txt.strip())
        if periodo_dto is None:
            return False, "Error al registrar el periodo.", []

        # Guardar cada fila — el service valida contra BD real
        ids_nuevos: list[int] = []
        for f in filas_validas:
            ok, msg, id_nuevo = self._service.guardar_horario(GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=f.dia,
                hora_inicio=f.hora_inicio,
                hora_fin=f.hora_fin,
                total_horas=f.delta,
                id_plan=self._id_plan,
                id_lies=self._state.id_lies_activa,
                id_semestre=id_sem,
            ))
            if not ok:
                return False, msg, []
            if id_nuevo is not None:
                ids_nuevos.append(id_nuevo)

        return True, "¡Horario agregado correctamente!", ids_nuevos

    # ── Editar horario ────────────────────────────────────────

    def iniciar_edicion(self, id_detalle: int) -> HorarioDetalleDTO | None:
        """Carga el detalle del horario para poblar el formulario.

        Args:
            id_detalle: ID del detalle (DetalleHorarioModel.id_detalle_horario).

        Returns:
            HorarioDetalleDTO si existe, None si no se encontró.
        """
        detalle = self._service.obtener_detalle_por_id(id_detalle)
        if detalle is None:
            return None
        self._state.editando_id_detalle = id_detalle
        return detalle

    def guardar_edicion(
        self,
        id_asig: str,
        id_aula: str,
        id_doc: str,
        periodo_txt: str,
        filas_validas: list[FilaHorarioDTO],
        id_sem: int | None,
    ) -> tuple[bool, str]:
        """Guarda los cambios del detalle en edición.

        Actualiza SOLO el detalle específico (por id_detalle_horario).
        La validación se hace en el backend via EditarHorarioUseCase.

        Returns:
            (True, mensaje_ok) o (False, mensaje_error).
        """
        if self._state.editando_id_detalle is None:
            return False, "No hay horario en edición."

        periodo_dto = self._service.crear_periodo(periodo_txt.strip())
        if periodo_dto is None:
            return False, "Error al registrar el periodo."

        # Actualizar el detalle específico (SIN crear filas adicionales)
        f0 = filas_validas[0]
        ok, msg = self._service.actualizar_detalle(
            id_detalle=self._state.editando_id_detalle,
            dto=GuardarHorarioDTO(
                id_asignacion=int(id_asig),
                id_docente=int(id_doc),
                id_aula=int(id_aula),
                id_periodo=periodo_dto.id,
                dia=f0.dia,
                hora_inicio=f0.hora_inicio,
                hora_fin=f0.hora_fin,
                total_horas=f0.delta,
                id_plan=self._id_plan,
                id_lies=self._state.id_lies_activa,
                id_semestre=id_sem,
            ),
        )
        if not ok:
            return False, msg

        return True, "¡Horario actualizado correctamente!"

    # ── Eliminar horario ──────────────────────────────────────

    def eliminar_horario(
        self, id_horario: int, id_sem_actual: int | None,
    ) -> tuple[bool, str]:
        """Elimina un horario.

        Returns:
            (True, mensaje_ok) o (False, mensaje_error).
        """
        ok, msg = self._service.eliminar_horario(id_horario)
        return ok, msg

    # ── Cargar ────────────────────────────────────────────────

    def cargar(self, id_plan: int) -> dict:
        """Carga los datos iniciales para la pantalla.

        Returns:
            Dict con: nombre_plan, semestres, lies, aulas, docentes, tipos.
        """
        return {
            "nombre_plan": self._service.obtener_nombre_plan(id_plan),
            "semestres":   self._service.obtener_semestres(id_plan),
            "lies":        self._service.obtener_lies_del_plan(id_plan),
            "aulas":       list(self._service.obtener_aulas()),
            "docentes":    list(self._service.obtener_docentes()),
            "tipos":       self._service.obtener_tipos_materia(),
        }

    def cargar_unidades(
        self,
        id_sem: int,
        id_lies: int,
        sem_opt_id: int | None,
        sin_limpiar: bool = False,
    ) -> list:
        """Carga unidades de aprendizaje para el semestre dado.

        Args:
            sin_limpiar: Si True, no limpia tabla ni cachés
                (usado al iniciar edición).

        Returns:
            Lista ordenada de UnidadAprendizajeDTO.
        """
        unidades = list(self._service.obtener_unidades(
            self._id_plan, id_lies, id_sem,
        ))
        if sem_opt_id:
            unidades += self._service.obtener_unidades(
                self._id_plan, id_lies, sem_opt_id,
            )
        unidades.sort(key=lambda u: (
            0 if u.tipo.lower().startswith("tronco") else 1, u.nombre,
        ))
        return unidades

    def cambiar_semestre(
        self,
        id_sem: int,
        id_lies: int,
        sem_opt_id: int | None,
    ) -> list:
        """Lógica al cambiar de semestre.

        Carga unidades y actualiza state.unidades.
        Ya no limpia cachés — la BD es la fuente de verdad.

        Returns:
            Lista ordenada de UnidadAprendizajeDTO.
        """
        unidades = self.cargar_unidades(id_sem, id_lies, sem_opt_id)
        self._state.unidades = unidades
        return unidades

    # ── PDF ───────────────────────────────────────────────────

    def datos_para_pdf(
        self,
        id_sem: int | None,
        sem_opt_id: int | None,
        all_lies: list,
    ) -> tuple | None:
        """Prepara los datos necesarios para generar el PDF.
        Usa BD como fuente única de verdad — sin filtrar por ids_sesion.

        Returns:
            (registros, nombre_plan, lies_nombre) o None si error.
        """
        if not id_sem:
            return None

        todos = self._service.obtener_horarios_filtrados(
            id_plan=self._id_plan,
            id_lies=self._state.id_lies_activa,
            id_semestre=id_sem,
            id_semestre_opt=sem_opt_id,
        )
        if not todos:
            return None

        nombre_plan = self._service.obtener_nombre_plan(self._id_plan)
        lies_nombre = next(
            (l.nombre for l in all_lies if l.id == self._state.id_lies_activa),
            "",
        )
        return todos, nombre_plan, lies_nombre

    # ── Crear catálogos ───────────────────────────────────────

    def crear_aula(self, nombre: str):
        """Crea una nueva aula. Retorna AulaDTO o None."""
        return self._service.crear_aula(nombre)

    def crear_docente(self, nombre: str):
        """Crea un nuevo docente. Retorna DocenteDTO o None."""
        return self._service.crear_docente(nombre)
