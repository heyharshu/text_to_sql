from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from src.config import Settings
from src.chat import small_talk, answer_question, json_value
from src.query_executor import QueryResult
from src.sql_generator import Candidate
from src.errors import AppError
from server import app

client = TestClient(app)
HEADERS = {"X-Chat-Client": "ask-your-data"}

@pytest.mark.parametrize("message", ["hi", "hlo", "Hello!", "thanks", "how are you", "bye"])
def test_greetings_skip_database(monkeypatch, message):
    def fail(*args):
        raise AssertionError("Greetings must not touch the database")
    monkeypatch.setattr("src.chat.inspect_schema", fail)
    assert answer_question(message, [], None, Settings(""))["status"] == "chat"

def test_question_returns_answer_and_executed_sql(monkeypatch, schema):
    monkeypatch.setattr("src.chat.inspect_schema", lambda _: schema)
    monkeypatch.setattr("src.chat.generate_sql", lambda *args: Candidate("sql", "SELECT COUNT(*) FROM orders", "Count orders.", ()))
    monkeypatch.setattr("src.chat.execute_query", lambda *args: QueryResult("SELECT COUNT(*) FROM public.orders LIMIT 200", ["orders"], [(42,)], 0.1, False))
    result = answer_question("Count orders", [], None, Settings(""))
    assert result["answer"] == "Orders: 42."
    assert result["sql"].endswith("LIMIT 200")
    assert result["rows"] == [[42]]

def test_clarification_and_followup(monkeypatch, schema):
    monkeypatch.setattr("src.chat.inspect_schema", lambda _: schema)
    def generate(client, question, *args):
        assert "Original question: Recent sales" in question
        assert "2025" in question
        return Candidate("clarification", "", "Which order statuses?", ())
    monkeypatch.setattr("src.chat.generate_sql", generate)
    pending = {"question": "Recent sales", "message": "Which date range?"}
    result = answer_question("2025", [], pending, Settings(""))
    assert result["pending"]["message"] == "Which order statuses?"

def test_api_greeting_works_without_config(monkeypatch):
    monkeypatch.setattr("server.load_settings", lambda: (_ for _ in ()).throw(AssertionError()))
    response = client.post("/api/chat", json={"message": "hlo"}, headers=HEADERS)
    assert response.status_code == 200 and response.json()["status"] == "chat"

def test_api_errors_are_readable(monkeypatch):
    def fail():
        raise AppError("Database is unavailable. Try again.")
    monkeypatch.setattr("server.load_settings", fail)
    response = client.post("/api/chat", json={"message": "Count orders"}, headers=HEADERS)
    assert response.status_code == 400
    assert response.json()["answer"] == "Database is unavailable. Try again."

def test_external_origin_rejected():
    response = client.post("/api/chat", json={"message": "hello"}, headers={**HEADERS, "Origin": "https://example.com"})
    assert response.status_code == 403

def test_missing_client_header_rejected():
    assert client.post("/api/chat", json={"message": "hello"}).status_code == 403

@pytest.mark.parametrize("body", [{"message": "x" * 2001}, {"message": "hello", "discount": "guess"}, {"message": "hello", "history": [{"question": "q", "sql": "s"}] * 5}])
def test_invalid_requests_rejected(body):
    assert client.post("/api/chat", json=body, headers=HEADERS).status_code == 422

def test_serialization_preserves_money_and_dates():
    assert json_value(Decimal("123.45")) == "123.45"
    assert json_value(date(2025, 1, 1)) == "2025-01-01"
