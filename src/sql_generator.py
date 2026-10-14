import json
from dataclasses import dataclass
from .errors import AppError
from .ollama_client import OllamaClient
from .prompt_builder import build_messages


@dataclass(frozen=True)
class Candidate:
    status: str
    sql: str
    message: str
    assumptions: tuple[str, ...]


def generate_sql(client: OllamaClient, question: str, schema: dict, rules: dict,
                 history: list[dict] | None = None) -> Candidate:
    question = question.strip()
    if not question or len(question) > 2000:
        raise AppError("Write a question between 1 and 2,000 characters.")
    raw = client.chat(build_messages(question, schema, rules, history))
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("status") not in {"sql", "clarification", "unsupported"}:
            raise ValueError
        sql, message, assumptions = data.get("sql", ""), data.get("message", ""), data.get("assumptions", [])
        if not isinstance(sql, str) or not isinstance(message, str) or not isinstance(assumptions, list):
            raise ValueError
        if not all(isinstance(item, str) for item in assumptions) or len(assumptions) > 10:
            raise ValueError
        if len(sql) > 20000 or len(message) > 2000 or any(len(item) > 500 for item in assumptions):
            raise ValueError
        if data["status"] == "sql" and not sql.strip():
            raise ValueError
        if data["status"] != "sql" and (sql.strip() or not message.strip()):
            raise ValueError
        return Candidate(data["status"], sql.strip(), message.strip(), tuple(assumptions))
    except (ValueError, TypeError):
        raise AppError("The model didn’t return a usable SQL response. Try rephrasing your question.") from None
