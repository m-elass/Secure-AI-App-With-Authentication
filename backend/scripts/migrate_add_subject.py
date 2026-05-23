"""
Migración: añade columna `subject` a la tabla `challenges`.

CUÁNDO EJECUTAR
───────────────
Una sola vez, tras desplegar la nueva versión del backend y ANTES de levantar
el servidor por primera vez. Si ya despliegas sobre una BD vacía (database.db
nuevo), no hace falta: SQLAlchemy creará la tabla con la columna.

USO
───
    cd backend
    python scripts/migrate_add_subject.py

Es idempotente: si la columna ya existe, no hace nada.
"""
import sqlite3
import sys
from pathlib import Path


def main():
    db_path = Path(__file__).resolve().parent.parent / "database.db"

    if not db_path.exists():
        print(f"[migrate] No existe {db_path}. La tabla se creará "
              f"limpia al arrancar el backend; nada que migrar.")
        return

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # ¿Existe la columna ya?
    cur.execute("PRAGMA table_info(challenges)")
    cols = [row[1] for row in cur.fetchall()]

    if "subject" in cols:
        print("[migrate] La columna 'subject' ya existe. Nada que hacer.")
        conn.close()
        return

    if "challenges" not in [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        print("[migrate] No existe la tabla 'challenges' todavía. Nada que migrar.")
        conn.close()
        return

    print("[migrate] Añadiendo columna 'subject'...")
    cur.execute("ALTER TABLE challenges ADD COLUMN subject TEXT NOT NULL DEFAULT 'per'")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_challenges_subject ON challenges(subject)")
    conn.commit()
    conn.close()

    print(f"[migrate] Listo. Todas las preguntas existentes quedan marcadas "
          f"como 'per'.")


if __name__ == "__main__":
    main()