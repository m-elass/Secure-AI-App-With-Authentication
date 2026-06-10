"""
Migración: añade columnas `subject` y `area` a la tabla `challenges`.

Es IDEMPOTENTE: ejecutar varias veces no causa problemas.

USO
───
    cd backend
    python scripts/migrate_db.py

Si la tabla aún no existe (despliegue limpio), no hace nada: SQLAlchemy
creará las columnas correctas en el primer arranque del backend.
"""
import sqlite3
from pathlib import Path


def main():
    db_path = Path(__file__).resolve().parent.parent / "database.db"

    if not db_path.exists():
        print(f"[migrate] No existe {db_path}. Nada que migrar.")
        return

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # ¿Existe la tabla?
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    if "challenges" not in tables:
        print("[migrate] No existe la tabla 'challenges'. Nada que migrar.")
        conn.close()
        return

    # Columnas actuales
    cur.execute("PRAGMA table_info(challenges)")
    cols = {row[1] for row in cur.fetchall()}

    # ── 1. subject ──
    if "subject" not in cols:
        print("[migrate] Añadiendo columna 'subject'...")
        cur.execute("ALTER TABLE challenges ADD COLUMN subject TEXT NOT NULL DEFAULT 'per'")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_challenges_subject ON challenges(subject)")
    else:
        print("[migrate] La columna 'subject' ya existe.")

    # ── 2. area ──
    if "area" not in cols:
        print("[migrate] Añadiendo columna 'area'...")
        # NULL para preguntas históricas (PER no tiene áreas; bioquímica
        # anteriores tampoco las tenían etiquetadas).
        cur.execute("ALTER TABLE challenges ADD COLUMN area TEXT")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_challenges_area ON challenges(area)")
    else:
        print("[migrate] La columna 'area' ya existe.")

    conn.commit()
    conn.close()
    print("[migrate] Listo.")


if __name__ == "__main__":
    main()