import pytest
from src.config import Settings
from src.errors import AppError
from src.query_executor import execute_query, QueryResult

def test_execution_rejects_before_connection(monkeypatch, schema):
    def unexpected(*args):
        raise AssertionError("Unsafe SQL must never reach the database")
    monkeypatch.setattr("src.query_executor.read_connection", unexpected)
    with pytest.raises(AppError):
        execute_query("DELETE FROM orders", schema, Settings("hidden"))

