"""
Migração pontual, idempotente: remove a coluna profile_id de job_records.

A feature de multi-profile foi descontinuada — todas as linhas já tinham
profile_id=NULL (confirmado antes de rodar isso), então não há dado a migrar,
só a coluna morta a remover.

Rodar uma única vez: python scripts/drop_profile_id_v1.py

Requisitos:
- SQLite >= 3.35 (ALTER TABLE ... DROP COLUMN nativo). Python 3.12 já embute
  uma versão recente o suficiente — confirme com:
  python -c "import sqlite3; print(sqlite3.sqlite_version)"
- PostgreSQL: qualquer versão suportada por este projeto já suporta
  DROP COLUMN IF EXISTS nativamente.
"""
from sqlalchemy import text
from app.db.session import engine


def main():
    dialect = engine.dialect.name

    with engine.connect() as conn:
        if dialect == "sqlite":
            existing_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(job_records)"))]
            if "profile_id" in existing_cols:
                conn.execute(text("ALTER TABLE job_records DROP COLUMN profile_id"))
                conn.commit()
                print("DELETE COLUMN profile_id (SQLite).")
            else:
                print("Column profile_id doesn't exist anymore")
        else:
            conn.execute(text("ALTER TABLE job_records DROP COLUMN IF EXISTS profile_id"))
            conn.commit()
            print("Column profile_id deleted or doesn't exists anymore — PostgreSQL.")


if __name__ == "__main__":
    main()