"""Small talk and database questions share one chat, but only SQL goes to Postgres."""
import re
from datetime import date, datetime
from decimal import Decimal
from .errors import AppError
from .ollama_client import OllamaClient
from .schema_inspector import inspect_schema
from .sql_generator import generate_sql
from .query_executor import execute_query


def small_talk(message: str) -> str | None:
    text = re.sub(r"[^a-z0-9\s]", "", message.lower()).strip()
    text = " ".join(text.split())
    if text in {"hi", "hii", "hiii", "hello", "hlo", "helo", "hey", "hey there", "hi there", "good morning", "good evening"}:
        return "Hey! What would you like to find out about your store? You can ask about orders, customers, products, or sales."
    if text in {"thanks", "thank you", "thankyou", "ty", "thanks a lot"}:
        return "You’re welcome! Anything else you’d like to check?"
    if text in {"how are you", "how are you doing", "how r u"}:
        return "Doing well, thanks for asking. Ready when you are—what shall we look up?"
    if text in {"bye", "goodbye", "see you"}:
        return "See you! Come back whenever you have another question."
    if text in {"help", "what can you do", "who are you"}:
        return "I help you explore your store’s data. Try ‘How many orders do we have by status?’ or ‘Which products earned the most revenue?’ You can view the SQL under each database answer."
    return None


def json_value(value):
    # Preserve numeric precision rather than silently rounding money into floats.
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def answer_question(message, history, pending, settings, revenue_scope="completed", discount="fraction"):
    greeting = small_talk(message)
    if greeting:
        return {"status": "chat", "answer": greeting, "pending": pending}
    effective = message
    if pending:
        effective = f"Original question: {pending['question']}\nClarification asked: {pending['message']}\nUser answer: {message}"
    if len(effective) > 2000:
        raise AppError("That clarification is getting long. Start a new chat and ask the question with the details included.")
    rules = {
        "discount_storage": discount,
        "revenue_order_statuses": ["completed"] if revenue_scope == "completed" else ["completed", "processing", "cancelled", "returned"],
        "revenue_formula": "quantity * order_items.unit_price * (1 - discount_percent)" if discount == "fraction" else "quantity * order_items.unit_price * (1 - discount_percent / 100.0)",
        "revenue_note": "Use sale price from order_items, not current products.unit_price. State the revenue status assumption.",
    }
    schema = inspect_schema(settings)
    candidate = generate_sql(OllamaClient(settings), effective, schema, rules, history)
    if candidate.status != "sql":
        return {"status": candidate.status, "answer": candidate.message,
                "pending": {"question": effective, "message": candidate.message} if candidate.status == "clarification" else None}
    result = execute_query(candidate.sql, schema, settings)
    rows = [[json_value(value) for value in row] for row in result.rows]
    if not rows:
        answer = "No matches this time. Try a wider date range or fewer filters."
    elif len(rows) == 1 and len(result.columns) == 1:
        label = result.columns[0].replace("_", " ")
        if label.startswith("col ") or label.startswith(" col "):
            label = "Result"
        answer = f"{label.capitalize()}: {rows[0][0] if rows[0][0] is not None else 'no value'}."
    else:
        answer = f"Here’s what I found—{len(rows)} {'row' if len(rows) == 1 else 'rows'} matched your question."
    return {"status": "result", "answer": answer, "sql": result.sql,
            "columns": result.columns, "rows": rows, "seconds": round(result.seconds, 3),
            "at_limit": result.at_limit, "assumptions": list(candidate.assumptions),
            "context": {"question": effective, "sql": result.sql}, "pending": None,
            "rules": {"revenue_scope": revenue_scope, "discount": discount}}
