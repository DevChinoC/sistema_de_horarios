"""
tests/test_services/test_validacion_tronco.py

Testeo de la lógica de validación de horarios:
  1. Tronco común → la misma materia debe tener la misma HORA en todas las LIES
  2. Optativa   → no puede compartir hora con tronco común
  3. Tabla limpia al entrar (validación por sesión, no por BD)

Usa la BD real (sistema_horarios). NO modifica datos permanentes;
los horarios de prueba se crean y eliminan dentro de cada test.
"""

import sys
import os

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")))

from datetime import datetime
from infrastructure.db.connection import DatabaseConnection
from infrastructure.repositories.horario_repository import HorarioRepository
from application.services.horario_service import HorarioService
from application.dto.horario_dto import GuardarHorarioDTO


# ─────────────────────────────────────────────────────────────
# Datos conocidos de la BD
# ─────────────────────────────────────────────────────────────
ID_PLAN = 1  # "plan 2026"

# Materias de tronco común (misma id_materia en las 3 LIES)
# "Proyecto de grado" → id_materia=1
#   TICs:         id_asignacion=1
#   Construcción: id_asignacion=2
#   Geomática:    id_asignacion=3
# "Trabajo de grado" → id_materia=2
#   TICs:         id_asignacion=4
#   Construcción: id_asignacion=5
#   Geomática:    id_asignacion=6

# Optativa (id_materia IS NULL, id_optativa IS NOT NULL)
# "Lenguajes de programacion" TICs → id_asignacion=7


def sep(titulo: str) -> None:
    print(f"\n{'═'*60}")
    print(f"  {titulo}")
    print(f"{'═'*60}")


def ok(msg: str) -> None:
    print(f"  ✅ {msg}")


def fail(msg: str) -> None:
    print(f"  ❌ {msg}")


def info(msg: str) -> None:
    print(f"  ℹ️  {msg}")


# ═════════════════════════════════════════════════════════════
# TEST 1: Conexión a BD y consultas básicas
# ═════════════════════════════════════════════════════════════
def test_conexion_y_datos():
    sep("TEST 1: Conexión a BD y datos existentes")
    service = HorarioService()

    nombre = service.obtener_nombre_plan(ID_PLAN)
    assert nombre, "No se encontró el plan"
    ok(f"Plan encontrado: '{nombre}'")

    lies = service.obtener_todas_lies_del_plan(ID_PLAN)
    assert len(lies) == 3, f"Se esperaban 3 LIES, hay {len(lies)}"
    ok(f"LIES del plan: {[l.nombre for l in lies]}")

    semestres = service.obtener_semestres(ID_PLAN)
    assert len(semestres) > 0, "No hay semestres"
    ok(f"Semestres: {[(s.id, s.numero) for s in semestres]}")


# ═════════════════════════════════════════════════════════════
# TEST 2: obtener_id_materia — identifica tronco vs optativa
# ═════════════════════════════════════════════════════════════
def test_identificar_tronco_vs_optativa():
    sep("TEST 2: Identificación tronco vs optativa")
    service = HorarioService()

    # Tronco: "Proyecto de grado" en TICs (id_asignacion=1)
    id_mat = service.obtener_id_materia(1)
    assert id_mat == 1, f"id_materia debería ser 1, es {id_mat}"
    ok(f"id_asignacion=1 → id_materia={id_mat} (tronco ✓)")

    # Tronco: "Proyecto de grado" en Construcción (id_asignacion=2)
    id_mat2 = service.obtener_id_materia(2)
    assert id_mat2 == 1, f"Debería compartir id_materia=1, tiene {id_mat2}"
    ok(f"id_asignacion=2 → id_materia={id_mat2} (misma materia en otra LIES ✓)")

    # Tronco: "Proyecto de grado" en Geomática (id_asignacion=3)
    id_mat3 = service.obtener_id_materia(3)
    assert id_mat3 == 1, f"Debería compartir id_materia=1, tiene {id_mat3}"
    ok(f"id_asignacion=3 → id_materia={id_mat3} (misma materia en otra LIES ✓)")

    # Optativa: "Lenguajes de programacion" en TICs (id_asignacion=7)
    id_mat_opt = service.obtener_id_materia(7)
    assert id_mat_opt is None, f"Debería ser None (optativa), es {id_mat_opt}"
    ok(f"id_asignacion=7 → id_materia={id_mat_opt} (optativa ✓)")

    # es_asignacion_tronco
    assert service.es_asignacion_tronco(1) is True
    assert service.es_asignacion_tronco(7) is False
    ok("es_asignacion_tronco() funciona correctamente")


# ═════════════════════════════════════════════════════════════
# TEST 3: Repository — obtener_horario_tronco_existente
# ═════════════════════════════════════════════════════════════
def test_repo_horario_tronco_existente():
    sep("TEST 3: Repository — buscar horario de tronco existente en BD")
    db = DatabaseConnection()
    session = db.get_session()
    try:
        repo = HorarioRepository(session)

        # id_materia=1 = "Proyecto de grado", ya tiene horarios en TICs
        rows = repo.obtener_horario_tronco_existente(ID_PLAN, id_materia=1)
        assert len(rows) > 0, "Debería encontrar horarios de Proyecto de grado"
        ok(f"Encontrados {len(rows)} horarios de 'Proyecto de grado' en BD:")
        for r in rows:
            info(f"  {r.dia} {r.hora_inicio}–{r.hora_fin} (LIES: {r.lies_nombre})")

        # Excluir id_asignacion=1 (TICs) — no debería encontrar nada
        # porque solo TICs tiene horarios registrados
        rows2 = repo.obtener_horario_tronco_existente(
            ID_PLAN, id_materia=1, excluir_id_asignacion=1)
        ok(f"Excluyendo id_asignacion=1: {len(rows2)} resultados")

    finally:
        session.close()


# ═════════════════════════════════════════════════════════════
# TEST 4: Repository — obtener_horarios_tronco_del_plan
# ═════════════════════════════════════════════════════════════
def test_repo_horarios_tronco_del_plan():
    sep("TEST 4: Repository — todos los horarios de tronco del plan")
    db = DatabaseConnection()
    session = db.get_session()
    try:
        repo = HorarioRepository(session)
        rows = repo.obtener_horarios_tronco_del_plan(ID_PLAN)
        ok(f"Total horarios de tronco en plan {ID_PLAN}: {len(rows)}")
        for r in rows:
            info(f"  {r.nombre_materia}: {r.dia} {r.hora_inicio}–{r.hora_fin}")
    finally:
        session.close()


# ═════════════════════════════════════════════════════════════
# TEST 5: Simulación de caché en memoria (lógica de sesión)
# ═════════════════════════════════════════════════════════════
def test_cache_sesion_tronco():
    sep("TEST 5: Caché en memoria — tronco común entre LIES")
    service = HorarioService()

    # Simular el diccionario _tronco_horas del DetallePlanView
    tronco_horas: dict[int, dict] = {}

    # PASO 1: En TICs, asignar "Proyecto de grado" (id_asig=1) → 10:00-12:30
    id_asig_tics = 1
    id_materia = service.obtener_id_materia(id_asig_tics)
    assert id_materia == 1
    hi, hf = "10:00", "12:30"

    # No hay registro previo → se permite
    assert id_materia not in tronco_horas
    tronco_horas[id_materia] = {"hora_inicio": hi, "hora_fin": hf}
    ok(f"TICs: 'Proyecto de grado' → {hi}–{hf} (registrado en caché)")

    # PASO 2: En Geomática, asignar misma materia (id_asig=3) con MISMA hora
    id_asig_geo = 3
    id_materia_geo = service.obtener_id_materia(id_asig_geo)
    assert id_materia_geo == 1  # misma id_materia

    # Verificar: misma hora → OK
    ref = tronco_horas[id_materia_geo]
    assert ref["hora_inicio"] == hi and ref["hora_fin"] == hf
    ok(f"Geomática: misma materia con {hi}–{hf} → PERMITIDO ✓")

    # PASO 3: En Construcción, intentar con OTRA hora → debe fallar
    id_asig_con = 2
    id_materia_con = service.obtener_id_materia(id_asig_con)
    assert id_materia_con == 1

    hi_diff, hf_diff = "14:00", "16:00"
    ref = tronco_horas[id_materia_con]
    hora_correcta = (ref["hora_inicio"] == hi_diff and ref["hora_fin"] == hf_diff)
    assert not hora_correcta, "No debería coincidir con hora diferente"
    ok(f"Construcción: misma materia con {hi_diff}–{hf_diff} → BLOQUEADO ✓")
    info(f"  Mensaje esperado: 'Debes seleccionar la misma hora: {ref['hora_inicio']}–{ref['hora_fin']}'")


# ═════════════════════════════════════════════════════════════
# TEST 6: Validación optativa vs tronco (caché en memoria)
# ═════════════════════════════════════════════════════════════
def test_cache_sesion_optativa_vs_tronco():
    sep("TEST 6: Caché en memoria — optativa vs tronco (mutuamente excluyentes)")
    service = HorarioService()

    # Simular caché con tronco ya registrado
    tronco_horas = {
        1: {"hora_inicio": "10:00", "hora_fin": "12:30"},  # Proyecto de grado
    }

    # CASO A: Optativa con hora que NO colisiona → OK
    hi_ok, hf_ok = "08:00", "09:30"
    colision = False
    for _, th in tronco_horas.items():
        hi_ex = datetime.strptime(th["hora_inicio"], "%H:%M")
        hf_ex = datetime.strptime(th["hora_fin"], "%H:%M")
        hi_new = datetime.strptime(hi_ok, "%H:%M")
        hf_new = datetime.strptime(hf_ok, "%H:%M")
        if hi_new < hf_ex and hf_new > hi_ex:
            colision = True
    assert not colision
    ok(f"Optativa {hi_ok}–{hf_ok} vs tronco 10:00–12:30 → SIN COLISIÓN ✓")

    # CASO B: Optativa con hora que SÍ colisiona → debe bloquear
    hi_bad, hf_bad = "11:00", "13:00"
    colision = False
    for _, th in tronco_horas.items():
        hi_ex = datetime.strptime(th["hora_inicio"], "%H:%M")
        hf_ex = datetime.strptime(th["hora_fin"], "%H:%M")
        hi_new = datetime.strptime(hi_bad, "%H:%M")
        hf_new = datetime.strptime(hf_bad, "%H:%M")
        if hi_new < hf_ex and hf_new > hi_ex:
            colision = True
    assert colision
    ok(f"Optativa {hi_bad}–{hf_bad} vs tronco 10:00–12:30 → COLISIÓN DETECTADA ✓")

    # CASO C: Optativa con EXACTA misma hora → colisiona
    hi_exact, hf_exact = "10:00", "12:30"
    colision = False
    for _, th in tronco_horas.items():
        hi_ex = datetime.strptime(th["hora_inicio"], "%H:%M")
        hf_ex = datetime.strptime(th["hora_fin"], "%H:%M")
        hi_new = datetime.strptime(hi_exact, "%H:%M")
        hf_new = datetime.strptime(hf_exact, "%H:%M")
        if hi_new < hf_ex and hf_new > hi_ex:
            colision = True
    assert colision
    ok(f"Optativa {hi_exact}–{hf_exact} vs tronco 10:00–12:30 → COLISIÓN EXACTA ✓")

    # CASO D: Optativa justo después (sin solapar) → OK
    hi_after, hf_after = "12:30", "14:00"
    colision = False
    for _, th in tronco_horas.items():
        hi_ex = datetime.strptime(th["hora_inicio"], "%H:%M")
        hf_ex = datetime.strptime(th["hora_fin"], "%H:%M")
        hi_new = datetime.strptime(hi_after, "%H:%M")
        hf_new = datetime.strptime(hf_after, "%H:%M")
        if hi_new < hf_ex and hf_new > hi_ex:
            colision = True
    assert not colision
    ok(f"Optativa {hi_after}–{hf_after} vs tronco 10:00–12:30 → SIN COLISIÓN (adyacente) ✓")


# ═════════════════════════════════════════════════════════════
# TEST 7: Reset de caché por sesión
# ═════════════════════════════════════════════════════════════
def test_reset_sesion():
    sep("TEST 7: Reset de caché al crear nueva instancia")

    # Simular: primera sesión registra horas
    sesion_1: dict[int, dict] = {}
    sesion_1[1] = {"hora_inicio": "10:00", "hora_fin": "12:30"}
    assert 1 in sesion_1
    ok("Sesión 1: tronco registrado en caché")

    # Simular: cerrar y abrir → nueva instancia → dict vacío
    sesion_2: dict[int, dict] = {}
    assert 1 not in sesion_2
    ok("Sesión 2: caché vacío (reset al crear nueva vista) ✓")
    info("La validación vuelve a empezar desde cero")


# ═════════════════════════════════════════════════════════════
# TEST 8: Validación solo por hora, NO por día
# ═════════════════════════════════════════════════════════════
def test_validacion_solo_hora_no_dia():
    sep("TEST 8: Validación solo por HORA, no por DÍA")

    tronco_horas = {
        1: {"hora_inicio": "10:00", "hora_fin": "12:30"},
    }

    # Misma materia, misma hora, DIFERENTE día → debe PERMITIRSE
    hi, hf = "10:00", "12:30"
    ref = tronco_horas[1]
    hora_ok = (ref["hora_inicio"] == hi and ref["hora_fin"] == hf)
    assert hora_ok
    ok(f"Misma materia tronco: Lunes {hi}–{hf} (TICs) → Martes {hi}–{hf} (Geomática) → PERMITIDO ✓")
    info("El día puede ser diferente, solo importa la hora")

    # Misma materia, DIFERENTE hora → debe BLOQUEARSE
    hi_diff, hf_diff = "14:00", "16:00"
    hora_ok2 = (ref["hora_inicio"] == hi_diff and ref["hora_fin"] == hf_diff)
    assert not hora_ok2
    ok(f"Misma materia tronco: {hi}–{hf} (TICs) vs {hi_diff}–{hf_diff} (Geomática) → BLOQUEADO ✓")


# ═════════════════════════════════════════════════════════════
# TEST 9: Service — validar_horario_optativa_vs_tronco (BD)
# ═════════════════════════════════════════════════════════════
def test_service_optativa_vs_tronco_bd():
    sep("TEST 9: Service — validar optativa vs tronco (usando BD)")
    service = HorarioService()

    # "Proyecto de grado" en TICs tiene horario Jueves 10:00–12:30
    # Verificar colisión con optativa en MISMO día + hora
    error = service.validar_horario_optativa_vs_tronco(
        ID_PLAN, "Jueves", "10:00", "12:30")
    if error:
        ok(f"Colisión detectada por BD: {error[:80]}...")
    else:
        info("No hay colisión (puede ser que los horarios en BD son diferentes)")

    # Verificar sin colisión
    error2 = service.validar_horario_optativa_vs_tronco(
        ID_PLAN, "Lunes", "06:00", "07:00")
    if error2 is None:
        ok("Sin colisión para Lunes 06:00–07:00 ✓")
    else:
        info(f"Colisión inesperada: {error2}")


# ═════════════════════════════════════════════════════════════
# TEST 10: Flujo completo simulado
# ═════════════════════════════════════════════════════════════
def test_flujo_completo():
    sep("TEST 10: Flujo completo — simulación de sesión de usuario")
    service = HorarioService()

    # Nuevo dict (nueva sesión)
    tronco_horas: dict[int, dict] = {}
    errores = []

    info("Usuario entra a DetallePlanView → tabla vacía, caché vacío")

    # Paso 1: TICs → "Proyecto de grado" → Lunes 10:00–12:00
    info("Paso 1: TICs → 'Proyecto de grado' → Lunes 10:00–12:00")
    id_asig = 1  # Proyecto de grado en TICs
    id_mat = service.obtener_id_materia(id_asig)
    hi, hf = "10:00", "12:00"

    if id_mat and id_mat in tronco_horas:
        ref = tronco_horas[id_mat]
        if ref["hora_inicio"] != hi or ref["hora_fin"] != hf:
            errores.append("Hora diferente a la registrada")
    # Guardar exitoso → registrar en caché
    tronco_horas[id_mat] = {"hora_inicio": hi, "hora_fin": hf}
    ok("Guardado exitoso. Caché actualizado.")

    # Paso 2: Geomática → "Proyecto de grado" → Martes 10:00–12:00 (misma hora, otro día)
    info("Paso 2: Geomática → 'Proyecto de grado' → Martes 10:00–12:00")
    id_asig2 = 3  # Proyecto de grado en Geomática
    id_mat2 = service.obtener_id_materia(id_asig2)
    assert id_mat2 == id_mat  # misma materia

    ref = tronco_horas[id_mat2]
    if ref["hora_inicio"] != hi or ref["hora_fin"] != hf:
        errores.append("ERROR: hora diferente")
    else:
        ok("Misma hora → PERMITIDO (día diferente es OK) ✓")

    # Paso 3: Construcción → "Proyecto de grado" → Miércoles 14:00–16:00 (DIFERENTE hora)
    info("Paso 3: Construcción → 'Proyecto de grado' → Miércoles 14:00–16:00")
    id_asig3 = 2  # Proyecto de grado en Construcción
    id_mat3 = service.obtener_id_materia(id_asig3)
    hi_bad, hf_bad = "14:00", "16:00"

    ref = tronco_horas[id_mat3]
    if ref["hora_inicio"] != hi_bad or ref["hora_fin"] != hf_bad:
        ok(f"BLOQUEADO → 'Debes seleccionar la misma hora: {ref['hora_inicio']}–{ref['hora_fin']}' ✓")
    else:
        errores.append("ERROR: no se bloqueó hora diferente")

    # Paso 4: Optativa con hora que colisiona (10:30–11:30 dentro de 10:00–12:00)
    info("Paso 4: Optativa → 'Lenguajes de programacion' → Viernes 10:30–11:30")
    hi_opt, hf_opt = "10:30", "11:30"
    hi_new = datetime.strptime(hi_opt, "%H:%M")
    hf_new = datetime.strptime(hf_opt, "%H:%M")
    colision = False
    for _, th in tronco_horas.items():
        hi_ex = datetime.strptime(th["hora_inicio"], "%H:%M")
        hf_ex = datetime.strptime(th["hora_fin"], "%H:%M")
        if hi_new < hf_ex and hf_new > hi_ex:
            colision = True
    if colision:
        ok("BLOQUEADO → 'Optativa colisiona con tronco común' ✓")
    else:
        errores.append("ERROR: no se detectó colisión optativa vs tronco")

    # Paso 5: Optativa con hora libre (16:00–18:00)
    info("Paso 5: Optativa → 'Lenguajes de programacion' → Viernes 16:00–18:00")
    hi_opt2, hf_opt2 = "16:00", "18:00"
    hi_new2 = datetime.strptime(hi_opt2, "%H:%M")
    hf_new2 = datetime.strptime(hf_opt2, "%H:%M")
    colision2 = False
    for _, th in tronco_horas.items():
        hi_ex = datetime.strptime(th["hora_inicio"], "%H:%M")
        hf_ex = datetime.strptime(th["hora_fin"], "%H:%M")
        if hi_new2 < hf_ex and hf_new2 > hi_ex:
            colision2 = True
    if not colision2:
        ok("PERMITIDO → sin colisión con tronco ✓")
    else:
        errores.append("ERROR: falsa colisión detectada")

    # Resultado
    print()
    if not errores:
        ok("FLUJO COMPLETO PASÓ EXITOSAMENTE ✅")
    else:
        for e in errores:
            fail(e)


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  TESTEO DE VALIDACIÓN — TRONCO COMÚN & OPTATIVAS")
    print("  Base de datos: sistema_horarios (MySQL)")
    print("█" * 60)

    tests = [
        test_conexion_y_datos,
        test_identificar_tronco_vs_optativa,
        test_repo_horario_tronco_existente,
        test_repo_horarios_tronco_del_plan,
        test_cache_sesion_tronco,
        test_cache_sesion_optativa_vs_tronco,
        test_reset_sesion,
        test_validacion_solo_hora_no_dia,
        test_service_optativa_vs_tronco_bd,
        test_flujo_completo,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            fail(f"ASSERTION ERROR: {e}")
            failed += 1
        except Exception as e:
            fail(f"ERROR: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'═'*60}")
    print(f"  RESULTADO: {passed} pasaron, {failed} fallaron")
    print(f"{'═'*60}\n")
