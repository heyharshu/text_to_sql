"""A fresh read-only transaction for every database operation."""
from contextlib import contextmanager
import psycopg
from .config import Settings
from .errors import AppError


@contextmanager
def read_connection(settings: Settings):
    try:
        # Connection keywords override URL options, including weaker SSL settings.
        with psycopg.connect(settings.database_url, connect_timeout=10, sslmode="require",
                             prepare_threshold=None, application_name="local_text_to_sql",
                             options="-c default_transaction_read_only=on") as connection:
            connection.read_only = True
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(settings.statement_timeout_ms),))
                cursor.execute("SELECT set_config('lock_timeout', %s, true)", ("2000",))
                cursor.execute("SELECT set_config('search_path', %s, true)", ("pg_catalog, public",))
            yield connection
            # Never retain transaction state, even after a successful SELECT.
            connection.rollback()
    except psycopg.errors.QueryCanceled:
        raise AppError("That query took too long. Try a smaller date range or a more specific question.") from None
    except psycopg.errors.InvalidPassword:
        raise AppError("Database sign-in failed. Check the pooler username and password in .env locally.") from None
    except psycopg.errors.InsufficientPrivilege:
        raise AppError("The database role cannot read one of these tables. Check its SELECT permissions and RLS policies.") from None
    except psycopg.OperationalError:
        raise AppError("Couldn’t connect to Supabase. Check your Session Pooler settings, network, and project status.") from None
    except psycopg.Error:
        raise AppError("PostgreSQL couldn’t run this query. Review the SQL and try rephrasing your question.") from None
