"""Local API and optional compiled React frontend. Start: python server.py"""
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
from src.config import load_settings
from src.chat import answer_question
from src.errors import AppError

app = FastAPI(title="Ask your data", docs_url=None, redoc_url=None, openapi_url=None)


class Context(BaseModel):
    question: str = Field(max_length=2000)
    sql: str = Field(max_length=20000)


class Clarification(BaseModel):
    question: str = Field(max_length=2000)
    message: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[Context] = Field(default_factory=list, max_length=4)
    pending: Clarification | None = None
    revenue_scope: Literal["completed", "all"] = "completed"
    discount: Literal["fraction", "percent"] = "fraction"


@app.middleware("http")
async def local_only(request: Request, call_next):
    # No cross-origin access, including requests from arbitrary websites to localhost.
    origin = request.headers.get("origin")
    host = request.headers.get("host", "")
    if host not in {"127.0.0.1:8000", "localhost:8000", "127.0.0.1:5173", "localhost:5173", "testserver"}:
        return JSONResponse({"answer": "Use the local app address."}, status_code=403)
    if origin and origin not in {"http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"}:
        return JSONResponse({"answer": "This app accepts requests from its local frontend only."}, status_code=403)
    if request.method == "POST" and request.headers.get("x-chat-client") != "ask-your-data":
        return JSONResponse({"answer": "Open the chat to send a question."}, status_code=403)
    return await call_next(request)


@app.exception_handler(AppError)
async def app_error(request, error):
    return JSONResponse({"status": "error", "answer": str(error)}, status_code=400)


@app.exception_handler(Exception)
async def unexpected_error(request, error):
    return JSONResponse({"status": "error", "answer": "Something went wrong while answering. Please try again."}, status_code=500)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(body: ChatRequest):
    if not body.message.strip():
        raise AppError("Type a message first.")
    # Greetings should work even when database configuration is missing.
    from src.chat import small_talk
    greeting = small_talk(body.message)
    if greeting:
        return {"status": "chat", "answer": greeting, "pending": body.pending.model_dump() if body.pending else None}
    return answer_question(body.message, [item.model_dump() for item in body.history],
                           body.pending.model_dump() if body.pending else None, load_settings(),
                           body.revenue_scope, body.discount)


DIST = Path(__file__).resolve().parent / "frontend" / "dist"
if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/")
def index():
    if (DIST / "index.html").exists():
        return FileResponse(DIST / "index.html")
    return JSONResponse({"message": "Run npm run dev in frontend, or npm run build to serve the compiled app here."})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False)
