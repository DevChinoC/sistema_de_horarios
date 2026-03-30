from sqlalchemy import text
from domain.models.plan_models import PlanEstudios


class PlanRepository:
    def __init__(self, db):
        self.db = db

    # =========================
    # CATALOGOS – NIVEL
    # =========================
    def obtener_niveles(self):
        return self.db.execute(text("""
            SELECT id_nivel, nombre
            FROM nivel_academico
            WHERE activo = 1
            ORDER BY nombre
        """)).fetchall()

    def crear_nivel(self, nombre: str) -> int:
        """Inserta un nuevo nivel académico y retorna su id."""
        result = self.db.execute(
            text("""
                INSERT INTO nivel_academico (nombre, activo)
                VALUES (:nombre, 1)
            """),
            {"nombre": nombre},
        )
        self.db.commit()
        return result.lastrowid

    # =========================
    # TIPO MATERIA
    # =========================
    def obtener_id_tipo(self, nombre: str):
        row = self.db.execute(
            text("""
                SELECT id_tipo
                FROM tipo_materia
                WHERE nombre=:nombre
            """),
            {"nombre": nombre},
        ).fetchone()

        if not row:
            raise ValueError(f"No existe tipo {nombre}")

        return row[0]

    # =========================
    # LIES – solo lectura interna
    # =========================
    def obtener_todas_lies(self) -> list[int]:
        """Retorna todos los id_lies activos. Un plan engloba todas las LIES."""
        rows = self.db.execute(
            text("""
                SELECT id_lies
                FROM lies_horarios
                WHERE activo = 1
                ORDER BY id_lies
            """)
        ).fetchall()
        if not rows:
            raise ValueError(
                "No hay registros en lies_horarios. "
                "Agrega al menos uno antes de crear un plan."
            )
        return [r[0] for r in rows]

    # =========================
    # PLAN
    # =========================
    def crear_plan(self, nombre: str, id_nivel: int):
        plan = PlanEstudios(
            nombre=nombre,
            id_nivel=id_nivel
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def vincular_plan_lies(self, id_plan: int, ids_lies: list[int]):
        """Vincula el plan con TODAS las LIES (relación N:M)."""
        for id_lies in ids_lies:
            self.db.execute(
                text("""
                    INSERT IGNORE INTO plan_lies (id_plan, id_lies)
                    VALUES (:id_plan, :id_lies)
                """),
                {"id_plan": id_plan, "id_lies": id_lies},
            )
        self.db.commit()

    # =========================
    # SEMESTRES BASE 0-8
    # =========================
    def crear_semestres_base(self, id_plan: int):
        for numero in range(0, 9):
            self.db.execute(
                text("""
                    INSERT INTO semestres (numero, id_plan)
                    VALUES (:numero, :id_plan)
                """),
                {
                    "numero": numero,
                    "id_plan": id_plan,
                },
            )
        self.db.commit()

    def obtener_semestre(self, numero: int, id_plan: int):
        row = self.db.execute(
            text("""
                SELECT id_semestre
                FROM semestres
                WHERE numero=:numero
                AND id_plan=:id_plan
            """),
            {
                "numero": numero,
                "id_plan": id_plan,
            }
        ).fetchone()

        if not row:
            raise ValueError(
                f"No existe semestre {numero} para plan {id_plan}"
            )

        return row[0]

    # =========================
    # DETALLE
    # =========================
    def crear_detalle(
        self,
        id_semestre: int,
        id_tipo: int,
        id_lies: int,
    ):
        result = self.db.execute(
            text("""
                INSERT INTO detalle_semestre
                (nombre_posicion, id_semestre, id_tipo, id_lies)
                VALUES ('AUTO', :id_semestre, :id_tipo, :id_lies)
            """),
            {
                "id_semestre": id_semestre,
                "id_tipo": id_tipo,
                "id_lies": id_lies,
            },
        )
        self.db.commit()
        return result.lastrowid

    # =========================
    # MATERIAS
    # =========================
    def guardar_materia(
        self,
        nombre: str,
        tipo: str,
        id_detalle: int,
        id_plan: int
    ):
        if tipo == "Optativa":
            result = self.db.execute(
                text("""
                    INSERT INTO optativas (nombre, id_plan)
                    VALUES (:nombre, :id_plan)
                """),
                {
                    "nombre": nombre,
                    "id_plan": id_plan
                }
            )
            id_optativa = result.lastrowid

            self.db.execute(
                text("""
                    INSERT INTO asignacion_materia
                    (id_detalle, id_optativa)
                    VALUES (:id_detalle, :id_optativa)
                """),
                {
                    "id_detalle": id_detalle,
                    "id_optativa": id_optativa,
                },
            )
        else:
            # Verificar si la materia ya existe antes de insertar
            row = self.db.execute(
                text("""
                    SELECT id_materia
                    FROM materias_tronco
                    WHERE nombre = :nombre
                """),
                {"nombre": nombre},
            ).fetchone()

            if row:
                id_materia = row[0]
            else:
                result = self.db.execute(
                    text("""
                        INSERT INTO materias_tronco (nombre)
                        VALUES (:nombre)
                    """),
                    {"nombre": nombre},
                )
                self.db.commit()
                id_materia = result.lastrowid

            self.db.execute(
                text("""
                    INSERT INTO asignacion_materia
                    (id_detalle, id_materia)
                    VALUES (:id_detalle, :id_materia)
                """),
                {
                    "id_detalle": id_detalle,
                    "id_materia": id_materia,
                },
            )

        self.db.commit()