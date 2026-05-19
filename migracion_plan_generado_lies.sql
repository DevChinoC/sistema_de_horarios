-- ============================================================
-- Migración: Agregar columna id_lies a plan_generado
-- Fecha: 2026-05-19
-- Bug: #2 — Historial fusiona las 3 LIES en un solo registro
-- ============================================================

-- Paso 1: Agregar columna nullable
ALTER TABLE plan_generado
  ADD COLUMN id_lies INT NULL AFTER id_periodo;

-- Paso 2: Agregar clave foránea
ALTER TABLE plan_generado
  ADD CONSTRAINT fk_plan_generado_lies
    FOREIGN KEY (id_lies) REFERENCES lies_horarios(id_lies);

-- ============================================================
-- Migración: Agregar columna id_semestre a detalle_horario
-- Bug: Optativas se guardaban con semestre 0 (del plan)
--      en vez del semestre seleccionado por el usuario
-- ============================================================

-- Paso 3: Agregar columna nullable a detalle_horario
ALTER TABLE detalle_horario
  ADD COLUMN id_semestre INT NULL AFTER id_asignacion;

-- Paso 4: Agregar clave foránea
ALTER TABLE detalle_horario
  ADD CONSTRAINT fk_detalle_horario_semestre
    FOREIGN KEY (id_semestre) REFERENCES semestres(id_semestre);

-- Paso 5: Backfill — asignar el semestre del plan a registros legacy
UPDATE detalle_horario dh
  JOIN asignacion_materia am ON am.id_asignacion = dh.id_asignacion
  JOIN detalle_semestre ds ON ds.id_detalle = am.id_detalle
SET dh.id_semestre = ds.id_semestre
WHERE dh.id_semestre IS NULL;

-- NOTA: Los registros existentes se backfillean con el semestre
-- de la estructura del plan. Los nuevos registros creados desde
-- la app tendrán id_semestre asignado correctamente al semestre
-- seleccionado por el usuario.
