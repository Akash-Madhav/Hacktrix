import logging
from sqlalchemy import text
from app.database import engine, Base, SessionLocal
import app.models  # Ensures all 24 models are registered with Base.metadata

logger = logging.getLogger("niriksha.database")

def clear_all_tables():
    """Completely empties all database tables while preserving the table schema."""
    # Ensure all tables exist in the database
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    is_sqlite = "sqlite" in engine.dialect.name.lower()
    is_postgres = "postgres" in engine.dialect.name.lower()

    print(f"[DB PURGE] Connecting to {engine.dialect.name.upper()} database...")
    print(f"[DB PURGE] Found {len(Base.metadata.sorted_tables)} tables in schema.")

    try:
        if is_postgres:
            # PostgreSQL: TRUNCATE with CASCADE
            table_names = [f'"{table.name}"' for table in Base.metadata.sorted_tables]
            if table_names:
                sql = f"TRUNCATE TABLE {', '.join(table_names)} RESTART IDENTITY CASCADE;"
                db.execute(text(sql))
                db.commit()
                print(f"[DB PURGE] Successfully truncated {len(table_names)} tables with CASCADE.")
        else:
            # SQLite: Disable foreign keys, delete all records, re-enable foreign keys
            db.execute(text("PRAGMA foreign_keys = OFF;"))
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(text(f'DELETE FROM "{table.name}";'))
            db.execute(text("PRAGMA foreign_keys = ON;"))
            db.commit()
            print(f"[DB PURGE] Successfully emptied all SQLite tables.")

        # Verify all tables are at 0 rows
        print("\n[DB PURGE VERIFICATION] Row count per table:")
        for table in Base.metadata.sorted_tables:
            count = db.execute(text(f'SELECT COUNT(*) FROM "{table.name}";')).scalar()
            print(f"  • {table.name}: {count} rows")
            assert count == 0, f"Table {table.name} is not empty!"

        print("\n[DB PURGE] All database tables are 100% EMPTY and ready for fresh production data.")

    except Exception as exc:
        db.rollback()
        print(f"[DB PURGE ERROR] Failed to empty tables: {exc}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_tables()
