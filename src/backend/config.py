"""
Libya B2B Platform - Configuration & Database Setup
Modular config extracted from main.py
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================
# DATABASE SETUP (PostgreSQL via DATABASE_URL, SQLite fallback)
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./libya_b2b.db")
IS_POSTGRES = DATABASE_URL.startswith("postgres")

if IS_POSTGRES:
    # Managed Postgres (e.g. Supabase pooler): no SQLite-specific connect_args
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables + add missing columns for existing tables."""
    from sqlalchemy import inspect, text

    Base.metadata.create_all(bind=engine)
    # Add missing columns to existing tables (SQLite ALTER TABLE limitation)
    inspector = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        if inspector.has_table(table_name):
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(engine.dialect)
                    nullable = "NULL" if col.nullable else "NOT NULL"
                    default = ""
                    if col.default is not None and col.default.is_clause_element:
                        default = f" DEFAULT {col.default.arg}"
                    try:
                        with engine.connect() as conn:
                            conn.execute(
                                text(
                                    f"ALTER TABLE {table_name} ADD COLUMN "
                                    f"{col.name} {col_type} {nullable}{default}"
                                )
                            )
                            conn.commit()
                    except Exception:
                        pass  # Column might already exist or other edge case

    # FTS5 full-text search is SQLite-only; Postgres uses ILIKE fallback (search.py)
    if not IS_POSTGRES:
        # Create FTS5 virtual table for product search
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
                        name, name_arabic, description, category,
                        content='products', content_rowid='id'
                    )"""
                    )
                )
                # Populate FTS table
                conn.execute(
                    text(
                        """INSERT OR REPLACE INTO products_fts(
                            rowid, name, name_arabic, description, category
                        )
                        SELECT id, name, name_arabic, description, category
                        FROM products WHERE is_active=1"""
                    )
                )
                conn.commit()
            # Create triggers to keep FTS in sync
            try:
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            """CREATE TRIGGER IF NOT EXISTS products_ai
                            AFTER INSERT ON products BEGIN
                            INSERT INTO products_fts(
                                rowid, name, name_arabic, description, category
                            )
                            VALUES (
                                new.id, new.name, new.name_arabic,
                                new.description, new.category
                            );
                        END"""
                        )
                    )
                    conn.execute(
                        text(
                            """CREATE TRIGGER IF NOT EXISTS products_ad
                            AFTER DELETE ON products BEGIN
                            INSERT INTO products_fts(
                                products_fts, rowid, name, name_arabic,
                                description, category
                            )
                            VALUES (
                                'delete', old.id, old.name, old.name_arabic,
                                old.description, old.category
                            );
                        END"""
                        )
                    )
                    conn.execute(
                        text(
                            """CREATE TRIGGER IF NOT EXISTS products_au
                            AFTER UPDATE ON products BEGIN
                            INSERT INTO products_fts(
                                products_fts, rowid, name, name_arabic,
                                description, category
                            )
                            VALUES (
                                'delete', old.id, old.name, old.name_arabic,
                                old.description, old.category
                            );
                            INSERT INTO products_fts(
                                rowid, name, name_arabic, description, category
                            )
                            VALUES (
                                new.id, new.name, new.name_arabic,
                                new.description, new.category
                            );
                        END"""
                        )
                    )
                    conn.commit()
            except Exception:
                pass
        except Exception:
            pass  # FTS5 might already exist


# ============================================================
# APP CONSTANTS
# ============================================================

APP_VERSION = "6.0.0"
API_VERSION = "1.0"
APP_TITLE = "Libya B2B Platform API"
APP_DESCRIPTION = "Offline-first KI-B2B-Plattform fuer Libyen — Alibaba Model"
