"""Fail closed: an explicit AST/function allowlist, then schema-aware resolution."""
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope
from .errors import AppError

NODES = set("""Select Union Intersect Except Subquery With CTE From Join Table
TableAlias Identifier Column Star Alias Literal Null Boolean Distinct Where Group
Having Order Ordered Limit Offset Paren And Or Not EQ NEQ GT GTE LT LTE Is In
Between Like ILike Add Sub Mul Div Mod Neg Case If Cast DataType DataTypeParam
Interval Window WindowSpec Tuple Exists Filter Var""".split())
FUNCTIONS = {"COUNT", "SUM", "AVG", "MIN", "MAX", "ROUND", "ABS", "COALESCE",
             "NULLIF", "LOWER", "UPPER", "LENGTH", "DATE_TRUNC", "TIMESTAMP_TRUNC",
             "EXTRACT", "CURRENT_DATE", "CURRENT_TIMESTAMP", "ROW_NUMBER", "RANK", "DENSE_RANK"}
TYPES = {"INT", "BIGINT", "SMALLINT", "DECIMAL", "FLOAT", "DOUBLE", "TEXT", "VARCHAR",
         "CHAR", "BOOLEAN", "DATE", "TIMESTAMP", "TIMESTAMPTZ", "INTERVAL"}


def validate_sql(sql: str, schema: dict, max_rows: int = 200) -> str:
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 20000:
        raise AppError("The generated SQL is empty or too long.")
    if not 1 <= max_rows <= 1000:
        raise AppError("The result limit must be between 1 and 1,000 rows.")
    try:
        statements = sqlglot.parse(sql, read="postgres")
        if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.Union, exp.Intersect, exp.Except)):
            raise AppError("Only one read-only SELECT statement is allowed.")
        tree = statements[0]
        for node in tree.walk():
            name = type(node).__name__
            if name in NODES:
                pass
            elif isinstance(node, exp.Func):
                function = node.name.upper() if isinstance(node, exp.Anonymous) else node.sql_name().upper()
                if function not in FUNCTIONS:
                    raise AppError("That SQL uses a function outside the supported analytics functions.")
            else:
                raise AppError("That SQL contains an unsupported or unsafe construct.")
            if isinstance(node, exp.With) and node.args.get("recursive"):
                raise AppError("Recursive queries aren’t supported.")
            if isinstance(node, exp.DataType) and node.this.value not in TYPES:
                raise AppError("That SQL uses an unsupported data type.")
            if isinstance(node, exp.Table) and (node.catalog or node.db not in {"", "public"} or not isinstance(node.this, exp.Identifier)):
                raise AppError("Queries may only read the approved public tables.")
            if isinstance(node, exp.Join) and (node.args.get("method") or node.args.get("kind") == "CROSS" or not (node.args.get("on") or node.args.get("using"))):
                raise AppError("Use an explicit join condition instead of a natural or cross join.")
        referenced = False
        for scope in traverse_scope(tree):
            for _, source in scope.sources.items():
                if isinstance(source, exp.Table):
                    if source.name not in schema["tables"]:
                        raise AppError("That SQL refers to a table outside the inspected e-commerce schema.")
                    referenced = True
        if not referenced:
            raise AppError("Ask a question that reads an e-commerce table.")
        mapping = {"public": {table: {column: meta["type"] for column, meta in columns.items()}
                              for table, columns in schema["tables"].items()}}
        # Resolves aliases/CTEs, expands stars, and rejects nonexistent/ambiguous columns.
        tree = qualify(tree, dialect="postgres", db="public", schema=mapping,
                       validate_qualify_columns=True, quote_identifiers=True)
        limit = tree.args.get("limit")
        if limit:
            value = limit.expression
            if not isinstance(value, exp.Literal) or value.is_string or not value.this.isdigit():
                raise AppError("The query limit must be a positive whole number.")
            if int(value.this) < 1:
                raise AppError("The query limit must be a positive whole number.")
            max_rows = min(max_rows, int(value.this))
        tree = tree.limit(max_rows)
        return tree.sql(dialect="postgres", pretty=True)
    except AppError:
        raise
    except (sqlglot.errors.SqlglotError, ValueError, TypeError, AttributeError, KeyError):
        raise AppError("The SQL couldn’t be matched to the live schema. Try naming the columns or tables more clearly.") from None
