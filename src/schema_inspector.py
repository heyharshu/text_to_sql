"""Discover actual columns and foreign keys; no data rows go into the prompt."""
from .config import Settings, TABLES
from .database import read_connection
from .errors import AppError


def inspect_schema(settings: Settings) -> dict:
    with read_connection(settings) as connection, connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.relname, a.attname, format_type(a.atttypid, a.atttypmod),
                   NOT a.attnotnull
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
            WHERE n.nspname = 'public' AND c.relkind = 'r'
              AND c.relname = ANY(%s) AND a.attnum > 0 AND NOT a.attisdropped
              AND has_column_privilege(c.oid, a.attname, 'SELECT')
            ORDER BY c.relname, a.attnum
        """, (list(TABLES),))
        tables = {}
        for table, column, data_type, nullable in cursor.fetchall():
            tables.setdefault(table, {})[column] = {"type": data_type, "nullable": nullable}
        if not tables:
            raise AppError("No readable e-commerce tables were found in public. Check the dataset and database permissions.")
        cursor.execute("""
            SELECT c.relname, con.conname, pg_get_constraintdef(con.oid)
            FROM pg_catalog.pg_constraint con
            JOIN pg_catalog.pg_class c ON c.oid = con.conrelid
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = ANY(%s)
              AND con.contype IN ('f', 'p', 'c')
            ORDER BY c.relname, con.conname
        """, (list(tables),))
        constraints = [{"table": t, "name": name, "definition": definition}
                       for t, name, definition in cursor.fetchall()]
    return {"schema": "public", "tables": tables, "constraints": constraints}
