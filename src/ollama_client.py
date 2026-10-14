"""Talk only to a loopback Ollama endpoint; ignore proxy environment variables."""
import requests
from .config import Settings
from .errors import AppError


class OllamaClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.request(method, self.settings.ollama_url + path,
                                           timeout=(5, self.settings.model_timeout_seconds),
                                           allow_redirects=False, **kwargs)
                if 300 <= response.status_code < 400:
                    raise AppError("Ollama returned a redirect. Use its direct local address in .env.")
                response.raise_for_status()
                return response.json()
        except requests.Timeout:
            raise AppError("The local model didn’t finish in time. Try a shorter question, or raise MODEL_TIMEOUT_SECONDS.") from None
        except (requests.RequestException, ValueError):
            raise AppError("Couldn’t get a response from Ollama. Make sure it’s running and qwen2.5:7b is installed.") from None

    def check(self) -> bool:
        payload = self._request("GET", "/api/tags")
        models = {item.get("name") for item in payload.get("models", [])}
        return self.settings.model in models

    def chat(self, messages: list[dict]) -> str:
        payload = self._request("POST", "/api/chat", json={
            "model": self.settings.model, "messages": messages,
            "format": "json", "stream": False,
            "options": {"temperature": 0, "num_predict": 1800, "num_ctx": 8192},
        })
        content = payload.get("message", {}).get("content")
        if not isinstance(content, str):
            raise AppError("Ollama returned an unexpected response. Please try again.")
        return content
