"""
Migração pontual, idempotente:
1) Cria as tabelas novas (skills, job_record_skills) — create_all já cobre
   isso para tabelas que ainda não existem.
2) Adiciona a coluna industry_fit em job_records, que JÁ EXISTE e por isso
   create_all não altera sozinho.
Rodar uma única vez: python scripts/add_skills_schema_v1.py
"""
from sqlalchemy import text
from app.db.session import engine, create_db_and_tables

def main():

    create_db_and_tables()  

    with engine.connect() as conn:
        dialect = engine.dialect.name

        if dialect == "sqlite":

            existing_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(job_records)"))]
            
            if "industry_fit" not in existing_cols:
                conn.execute(text("ALTER TABLE job_records ADD COLUMN industry_fit VARCHAR"))
                conn.commit()
                print("Coluna industry_fit adicionada.")
            else:
                print("Coluna industry_fit já existe — nada a fazer.")
                
        else:
            conn.execute(text("ALTER TABLE job_records ADD COLUMN IF NOT EXISTS industry_fit VARCHAR"))
            conn.commit()
            print("Coluna industry_fit adicionada (ou já existia).")


if __name__ == "__main__":
    main()