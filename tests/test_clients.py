import json
import pytest
from src.config import Settings, load_settings
from src.errors import AppError
from src.ollama_client import OllamaClient
from src.sql_generator import generate_sql

class FakeClient:
    def __init__(self, response):
        self.response = response
    def chat(self, messages):
        return self.response

@pytest.mark.parametrize("payload", ["no sql", "[]", '{"status":"sql","sql":""}', '{"status":"sql","sql":12}', '{"status":"clarification","sql":"SELECT 1","message":"why?"}'])
def test_bad_model_responses(payload, schema):
    with pytest.raises(AppError):
        generate_sql(FakeClient(payload), "Count orders", schema, {})

def test_clarification(schema):
    candidate = generate_sql(FakeClient(json.dumps({"status": "clarification", "sql": "", "message": "Which date range?", "assumptions": []})), "Recent sales", schema, {})
    assert candidate.status == "clarification"

@pytest.mark.parametrize("url", ["https://example.com", "http://127.0.0.1.evil.com", "http://user:pass@localhost:11434", "http://localhost:11434/path", "http://localhost:11434?redirect=remote"])
def test_external_models_rejected(monkeypatch, url):
    monkeypatch.setenv("DATABASE_URL", "postgresql://placeholder")
    monkeypatch.setenv("OLLAMA_URL", url)
    with pytest.raises(AppError):
        load_settings()

def test_no_proxy_or_redirects(monkeypatch):
    import requests
    def fake_request(self, method, url, **kwargs):
        assert self.trust_env is False
        assert kwargs["allow_redirects"] is False
        return type("Response", (), {"status_code": 302})()
    monkeypatch.setattr(requests.Session, "request", fake_request)
    with pytest.raises(AppError, match="redirect"):
        OllamaClient(Settings("hidden")).check()

def test_credentials_not_in_repr():
    assert "super_secret" not in repr(Settings("postgresql://super_secret"))
