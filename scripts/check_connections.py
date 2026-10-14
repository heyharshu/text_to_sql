"""Safe diagnostics: never print connection URLs, rows, or raw exceptions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import load_settings
from src.schema_inspector import inspect_schema
from src.ollama_client import OllamaClient
from src.errors import AppError

def main():
    settings = load_settings()
    failed = False
    for label, check in (("Supabase", lambda: inspect_schema(settings)), ("Ollama", lambda: OllamaClient(settings).check())):
        try:
            result = check()
            if result is False:
                print(f"{label}: server reachable, configured model not found.")
                failed = True
            else:
                print(f"{label}: ready.")
                if isinstance(result, dict):
                    print(f"Live schema: {len(result['tables'])} tables, {sum(len(c) for c in result['tables'].values())} readable columns.")
        except AppError as error:
            print(f"{label}: {error}")
            failed = True
    return int(failed)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except AppError as error:
        print(str(error))
        sys.exit(1)
