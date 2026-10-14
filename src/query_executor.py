"""Always validate at the execution boundary, even when the UI already did."""
from dataclasses import dataclass
from time import perf_counter
from .config import Settings
from .database import read_connection
from .sql_validator import validate_sql


@dataclass
class QueryResult:
    sql: str
    columns: list[str]
    rows: list[tuple]
    seconds: float
    at_limit: bool


def execute_query(sql: str, schema: dict, settings: Settings) -> QueryResult:
    safe_sql = validate_sql(sql, schema, settings.max_rows)
    start = perf_counter()
    with read_connection(settings) as connection, connection.cursor() as cursor:
        cursor.execute(safe_sql)
        columns = [column.name for column in cursor.description]
        rows = cursor.fetchmany(settings.max_rows)
    return QueryResult(safe_sql, columns, rows, perf_counter() - start, len(rows) == settings.max_rows)
