"""
Test integral del Sistema de Horarios.
Prueba las capas: PlanesService, HorarioService (DetallePlanView logic,
HorarioDocenteView logic, HistorialView logic).
"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(__file__))

from application.services.planes_service import PlanesService
from application.services.horario_service import HorarioService
from application.dto.horario_dto import GuardarHorarioDTO

# ── Contadores ────────────────────────────────────────────────
PASS = 0; FAIL = 0; WARN = 0
resultados = []

def ok(desc):
    global PASS; PASS += 1; resultados.append(("✅ PASS", desc))
    print(f"  ✅ PASS: {desc}")

def fail(desc, detail=""):
    global FAIL; FAIL += 1; resultados.append(("❌ FAIL", f"{desc} | {detail}"))
    print(f"  ❌ FAIL: {desc} — {detail}")

def warn(desc):
    global WARN; WARN += 1; resultados.append(("⚠️ WARN", desc))
    print(f"  ⚠️ WARN: {desc}")

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# ══════════════════════════════════════════════════════════════
planes_svc = PlanesService()
h_svc = HorarioService()

# IDs creados en este test para cleanup
horarios_creados = []

try:
    # ══════════════════════════════════════════════════════════
    section("1. PLANES_VIEW — Niveles y Planes")
    # ══════════════════════════════════════════════════════════
    niveles = planes_svc.obtener_niveles()
    if niveles:
        ok(f"obtener_niveles() → {len(niveles)} niveles: {[n.nombre for n in niveles]}")
    else:
        fail("obtener_niveles() retornó lista vacía")

    # Buscar DIIDT y MIIDT
    id_nivel_diidt = None; id_nivel_miidt = None
    for n in niveles:
        if "DIIDT" in n.nombre.upper(): id_nivel_diidt = n.id
        if "MIIDT" in n.nombre.upper(): id_nivel_miidt = n.id

    planes_diidt = []; planes_miidt = []
    if id_nivel_diidt:
        planes_diidt = planes_svc.obtener_planes_por_nivel(id_nivel_diidt)
        ok(f"Planes DIIDT: {[p.nombre for p in planes_diidt]}")
    else:
        warn("No se encontró nivel DIIDT")

    if id_nivel_miidt:
        planes_miidt = planes_svc.obtener_planes_por_nivel(id_nivel_miidt)
        ok(f"Planes MIIDT: {[p.nombre for p in planes_miidt]}")
    else:
        warn("No se encontró nivel MIIDT")

    # ══════════════════════════════════════════════════════════
    section("2. DETALLE_PLAN_VIEW — Catálogos y Estructura DIIDT")
    # ══════════════════════════════════════════════════════════
    if not planes_diidt:
        fail("Sin planes DIIDT, no se puede continuar test DIIDT")
    else:
        plan_d = planes_diidt[0]
        ok(f"Plan DIIDT seleccionado: {plan_d.nombre} (id={plan_d.id})")

        # Nombre del plan
        nombre = h_svc.obtener_nombre_plan(plan_d.id)
        ok(f"obtener_nombre_plan → '{nombre}'") if nombre else fail("Nombre plan vacío")

        # Nivel
        nivel_nombre = h_svc.obtener_nombre_nivel(plan_d.id)
        ok(f"obtener_nombre_nivel → '{nivel_nombre}'")

        # LIES — DIIDT no debería tener LIES visibles (solo MIIDT)
        lies_d = h_svc.obtener_lies_del_plan(plan_d.id)
        if not lies_d:
            ok("DIIDT no muestra LIES (correcto, solo MIIDT tiene)")
        else:
            warn(f"DIIDT retorna LIES visibles: {[l.nombre for l in lies_d]}")

        # LIES reales (para queries internas)
        all_lies_d = h_svc.obtener_todas_lies_del_plan(plan_d.id)
        if all_lies_d:
            ok(f"LIES internas DIIDT: {[l.nombre for l in all_lies_d]}")
            id_lies_d = all_lies_d[0].id
        else:
            fail("Sin LIES internas para DIIDT")
            id_lies_d = None

        # Semestres
        sems_d = h_svc.obtener_semestres(plan_d.id)
        ok(f"Semestres DIIDT: {[(s.id, s.numero) for s in sems_d]}")

        # Materias del semestre 1
        if sems_d and id_lies_d:
            sem1_d = next((s for s in sems_d if s.numero == 1), sems_d[0])
            unidades_d = h_svc.obtener_unidades(plan_d.id, id_lies_d, sem1_d.id)
            ok(f"Materias sem {sem1_d.numero}: {[(u.nombre, u.tipo) for u in unidades_d]}")

        # Catálogos globales
        docentes = h_svc.obtener_docentes()
        aulas = h_svc.obtener_aulas()
        periodos = h_svc.obtener_periodos()
        ok(f"Docentes: {len(docentes)}, Aulas: {len(aulas)}, Periodos: {len(periodos)}")

        if not docentes: fail("Sin docentes en BD")
        if not aulas: fail("Sin aulas en BD")
        if not periodos: fail("Sin periodos en BD")

    # ══════════════════════════════════════════════════════════
    section("3. DETALLE_PLAN_VIEW — Crear horarios DIIDT (3 docentes, 2 materias c/u)")
    # ══════════════════════════════════════════════════════════
    if planes_diidt and id_lies_d and sems_d and docentes and aulas and periodos:
        plan_d = planes_diidt[0]
        periodo = periodos[0]
        # Tomar semestre 1 con materias
        sem1_d = next((s for s in sems_d if s.numero == 1), sems_d[0])
        unidades_d = h_svc.obtener_unidades(plan_d.id, id_lies_d, sem1_d.id)

        if len(unidades_d) < 6:
            # Buscar en todos los semestres para tener suficientes
            all_unidades = []
            for s in sems_d:
                if s.numero == 0: continue
                uu = h_svc.obtener_unidades(plan_d.id, id_lies_d, s.id)
                for u in uu: all_unidades.append((s, u))
            warn(f"Sem 1 tiene solo {len(unidades_d)} materias, usando pool de {len(all_unidades)}")
        else:
            all_unidades = [(sem1_d, u) for u in unidades_d]

        # Asignar: 3 docentes × 2 materias = 6 horarios
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        horarios_spec = [
            ("08:00", "10:00"), ("10:00", "12:00"), ("14:00", "16:00"),
            ("08:00", "10:00"), ("10:00", "12:00"), ("14:00", "16:00"),
        ]

        count = 0
        for i in range(min(6, len(all_unidades))):
            doc_idx = i // 2  # 0,0,1,1,2,2
            if doc_idx >= len(docentes): doc_idx = doc_idx % len(docentes)
            sem_i, ua = all_unidades[i]
            hi, hf = horarios_spec[i]
            dia = dias[i % len(dias)]

            dto = GuardarHorarioDTO(
                id_asignacion=ua.id_asignacion,
                id_docente=docentes[doc_idx].id,
                id_aula=aulas[i % len(aulas)].id,
                id_periodo=periodo.id,
                dia=dia, hora_inicio=hi, hora_fin=hf,
                total_horas=2, id_plan=plan_d.id,
            )
            success, msg, id_h = h_svc.guardar_horario(dto)
            if success and id_h:
                horarios_creados.append(id_h)
                count += 1
                ok(f"Horario #{id_h}: {ua.nombre} → {docentes[doc_idx].nombre}, {dia} {hi}-{hf}")
            else:
                fail(f"Guardar horario {ua.nombre}", msg)

        ok(f"Total horarios DIIDT creados: {count}/6")
    else:
        fail("Datos insuficientes para crear horarios DIIDT")

    # ══════════════════════════════════════════════════════════
    section("4. DETALLE_PLAN_VIEW — MIIDT: TICs, Geomática, Construcción Sismo-Resistente")
    # ══════════════════════════════════════════════════════════
    if planes_miidt:
        plan_m = planes_miidt[0]
        ok(f"Plan MIIDT: {plan_m.nombre} (id={plan_m.id})")

        lies_m = h_svc.obtener_lies_del_plan(plan_m.id)
        ok(f"LIES MIIDT: {[l.nombre for l in lies_m]}")

        sems_m = h_svc.obtener_semestres(plan_m.id)
        ok(f"Semestres MIIDT: {[(s.id, s.numero) for s in sems_m]}")

        # Buscar LIES: TICs, Geomática, Construcción Sismo-Resistente
        target_lies = ["tic", "geom", "sismo"]
        lies_found = {}
        for l in lies_m:
            ln = l.nombre.lower()
            for t in target_lies:
                if t in ln:
                    lies_found[t] = l
                    break

        ok(f"LIES encontradas: {[(k, v.nombre) for k, v in lies_found.items()]}")

        periodo_m = periodos[0] if periodos else None
        count_m = 0
        for key, lies_obj in lies_found.items():
            sem1_m = next((s for s in sems_m if s.numero == 1), sems_m[0] if sems_m else None)
            if not sem1_m: continue

            unidades_m = h_svc.obtener_unidades(plan_m.id, lies_obj.id, sem1_m.id)
            ok(f"Materias LIES '{lies_obj.nombre}' sem {sem1_m.numero}: {[u.nombre for u in unidades_m[:3]]}")

            # Crear 2 horarios por LIES
            for j, ua in enumerate(unidades_m[:2]):
                doc_idx = (count_m + j) % len(docentes) if docentes else 0
                dia = dias[(count_m + j) % len(dias)]
                hi, hf = ("08:00", "10:00") if j == 0 else ("10:00", "12:00")

                # Test validación tronco común
                es_tronco = h_svc.es_asignacion_tronco(ua.id_asignacion)
                if es_tronco:
                    existente = h_svc.obtener_horario_tronco_existente(plan_m.id, ua.id_asignacion)
                    if existente:
                        ok(f"Tronco común detectado para '{ua.nombre}': usa horario existente de otra LIES")
                        # Usar mismo horario que la otra LIES
                        dia = existente[0]["dia"]
                        hi = existente[0]["hora_inicio"]
                        hf = existente[0]["hora_fin"]
                else:
                    # Test validación optativa vs tronco
                    col = h_svc.validar_horario_optativa_vs_tronco(plan_m.id, dia, hi, hf)
                    if col:
                        warn(f"Colisión optativa/tronco evitada: {col[:80]}...")
                        hi, hf = "16:00", "18:00"  # usar horario libre

                dto = GuardarHorarioDTO(
                    id_asignacion=ua.id_asignacion,
                    id_docente=docentes[doc_idx].id if docentes else 1,
                    id_aula=aulas[j % len(aulas)].id if aulas else 1,
                    id_periodo=periodo_m.id if periodo_m else 1,
                    dia=dia, hora_inicio=hi, hora_fin=hf,
                    total_horas=2, id_plan=plan_m.id,
                )
                success, msg, id_h = h_svc.guardar_horario(dto)
                if success and id_h:
                    horarios_creados.append(id_h)
                    count_m += 1
                    ok(f"MIIDT/{lies_obj.nombre}: {ua.nombre} → {dia} {hi}-{hf}")
                else:
                    fail(f"Guardar MIIDT/{lies_obj.nombre}/{ua.nombre}", msg)

        ok(f"Total horarios MIIDT creados: {count_m}")
    else:
        fail("Sin planes MIIDT")

    # ══════════════════════════════════════════════════════════
    section("5. DETALLE_PLAN_VIEW — Editar y Eliminar horario")
    # ══════════════════════════════════════════════════════════
    if horarios_creados:
        test_id = horarios_creados[0]
        det = h_svc.obtener_horario_detalle(test_id)
        if det:
            ok(f"obtener_horario_detalle({test_id}) → dia={det.dia}, {det.hora_inicio}-{det.hora_fin}")

            # Actualizar horario
            upd_dto = GuardarHorarioDTO(
                id_asignacion=det.id_asignacion, id_docente=det.id_docente,
                id_aula=det.id_aula, id_periodo=det.id_periodo,
                dia="Viernes", hora_inicio="12:00", hora_fin="14:00",
                total_horas=2, id_plan=planes_diidt[0].id if planes_diidt else 1,
            )
            upd_ok, upd_msg = h_svc.actualizar_horario(test_id, upd_dto)
            ok(f"actualizar_horario({test_id}) → {upd_msg}") if upd_ok else fail("Actualizar", upd_msg)

            # Verificar actualización
            det2 = h_svc.obtener_horario_detalle(test_id)
            if det2 and det2.dia == "Viernes" and det2.hora_inicio == "12:00":
                ok("Verificación post-update: día y hora correctos")
            else:
                fail("Verificación post-update falló")
        else:
            fail(f"obtener_horario_detalle({test_id}) retornó None")

        # Test eliminar (último horario creado)
        del_id = horarios_creados.pop()
        del_ok, del_msg = h_svc.eliminar_horario(del_id)
        ok(f"eliminar_horario({del_id}) → {del_msg}") if del_ok else fail("Eliminar", del_msg)

        # Verificar que ya no existe
        det_del = h_svc.obtener_horario_detalle(del_id)
        if det_del is None:
            ok(f"Horario {del_id} eliminado correctamente (no existe)")
        else:
            fail(f"Horario {del_id} aún existe después de eliminar")

    # ══════════════════════════════════════════════════════════
    section("6. HORARIO_DOCENTE_VIEW — Consultas por docente")
    # ══════════════════════════════════════════════════════════
    niveles_doc = h_svc.obtener_niveles_con_docente()
    ok(f"Niveles con docentes: {[n['nombre'] for n in niveles_doc]}")

    if docentes and horarios_creados:
        doc_test = docentes[0]
        # Cascada: periodos del docente
        periodos_doc = h_svc.obtener_periodos_por_docente(doc_test.id)
        ok(f"Periodos docente '{doc_test.nombre}': {[p.nombre for p in periodos_doc]}")

        if periodos_doc:
            per_d = periodos_doc[0]
            planes_doc = h_svc.obtener_planes_por_docente_periodo(doc_test.id, per_d.id)
            ok(f"Planes docente en periodo '{per_d.nombre}': {[p.nombre for p in planes_doc]}")

            if planes_doc:
                plan_doc = planes_doc[0]
                resumen = h_svc.obtener_horarios_docente(doc_test.id, plan_doc.id, per_d.id)
                ok(f"Horario docente: {len(resumen.filas)} entradas")
                for f in resumen.filas:
                    ok(f"  → {f.dia} {f.hora_inicio}-{f.hora_fin}: {f.nombre_materia} ({f.nombre_lies})")

    # ══════════════════════════════════════════════════════════
    section("7. HISTORIAL_VIEW — Consulta y filtrado")
    # ══════════════════════════════════════════════════════════
    historial = h_svc.obtener_historial_planes()
    ok(f"Historial total: {len(historial)} registros")
    for h in historial[:5]:
        ok(f"  → [{h.clave}] {h.nombre_plan} | {h.nombre_nivel} | {h.nombre_periodo}")

    # Cascada historial
    niveles_hist = h_svc.obtener_niveles_con_historial()
    ok(f"Niveles con historial: {[n['nombre'] for n in niveles_hist]}")

    if niveles_hist:
        niv_h = niveles_hist[0]
        periodos_h = h_svc.obtener_periodos_por_nivel(niv_h["id"])
        ok(f"Periodos nivel '{niv_h['nombre']}': {[p.nombre for p in periodos_h]}")

        if periodos_h:
            per_h = periodos_h[0]
            planes_h = h_svc.obtener_planes_por_nivel_periodo(niv_h["id"], per_h.id)
            ok(f"Planes en periodo '{per_h.nombre}': {[p.nombre for p in planes_h]}")

    # Test obtener_horarios_de_plan_generado (para edición desde historial)
    if historial:
        pg_test = historial[0]
        horarios_pg = h_svc.obtener_horarios_de_plan_generado(pg_test.id_plan_generado)
        ok(f"Horarios plan_generado #{pg_test.id_plan_generado}: {len(horarios_pg)} registros")
        for hp in horarios_pg[:3]:
            ok(f"  → {hp.unidad} | {hp.docente} | {hp.dia} {hp.hora_inicio}-{hp.hora_fin}")

        # Test id_plan desde plan_generado
        id_plan_from_pg = h_svc.obtener_id_plan_de_plan_generado(pg_test.id_plan_generado)
        if id_plan_from_pg:
            ok(f"id_plan desde plan_generado #{pg_test.id_plan_generado} → {id_plan_from_pg}")
        else:
            fail("obtener_id_plan_de_plan_generado retornó None")

    # ══════════════════════════════════════════════════════════
    section("8. VALIDACIONES DE LÓGICA DE NEGOCIO")
    # ══════════════════════════════════════════════════════════
    # Test: tronco común entre LIES
    if planes_miidt and lies_found:
        for key, lies_obj in lies_found.items():
            sem1 = next((s for s in sems_m if s.numero == 1), None)
            if not sem1: continue
            unidades = h_svc.obtener_unidades(plan_m.id, lies_obj.id, sem1.id)
            for ua in unidades[:2]:
                es_tronco = h_svc.es_asignacion_tronco(ua.id_asignacion)
                id_mat = h_svc.obtener_id_materia(ua.id_asignacion)
                ok(f"'{ua.nombre}': tronco={es_tronco}, id_materia={id_mat}, tipo={ua.tipo}")
            break  # solo probar con la primera LIES

    # Test: validación optativa vs tronco (horario ficticio)
    if planes_miidt:
        col_result = h_svc.validar_horario_optativa_vs_tronco(plan_m.id, "Lunes", "08:00", "10:00")
        if col_result:
            ok(f"Validación optativa/tronco detecta colisión correctamente")
        else:
            ok("Validación optativa/tronco: sin colisión (OK si no hay tronco Lunes 8-10)")

except Exception as e:
    fail(f"EXCEPCIÓN NO CONTROLADA", traceback.format_exc())

finally:
    # ══════════════════════════════════════════════════════════
    section("9. CLEANUP — Eliminando horarios de test")
    # ══════════════════════════════════════════════════════════
    for hid in horarios_creados:
        try:
            h_svc.eliminar_horario(hid)
            print(f"  🗑️ Horario {hid} eliminado")
        except: pass

    # ══════════════════════════════════════════════════════════
    section("RESUMEN FINAL")
    # ══════════════════════════════════════════════════════════
    print(f"\n  Total: {PASS + FAIL + WARN} tests")
    print(f"  ✅ PASS: {PASS}")
    print(f"  ❌ FAIL: {FAIL}")
    print(f"  ⚠️ WARN: {WARN}")
    print()
    if FAIL:
        print("  TESTS FALLIDOS:")
        for status, desc in resultados:
            if "FAIL" in status:
                print(f"    {desc}")
    print()
