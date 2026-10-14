# Ask your data

A Text-to-SQL chat app by Harsh Gupta.

Ask a question about the store's data, such as "Which 10 products earned the most
revenue?", and the app writes SQL, checks it, and fetches the answer from PostgreSQL.
The result appears in the chat with a table and a View SQL option. You can inspect
the exact query, copy it, or download the results as CSV.

The model runs locally through Ollama. Supabase hosts the database. This is a
learning and portfolio project built around a synthetic e-commerce dataset.

## What you can do

- Ask about orders, products, customers, and sales.
- Use questions that need joins, filters, totals, sorting, or date ranges.
- Inspect the SQL behind a database answer.
- Reply to a clarifying question when a metric or date range is unclear.
- Ask follow-up questions using the recent conversation as context.
- Say `hi`, `hlo`, or `how are you`. These greetings use local responses and skip
  the model and database.

Conversations stay in the page's memory. Refreshing starts a fresh chat; the app
keeps no saved conversation history in local storage. It sends the last four
executed questions and their SQL to the model for follow-ups, without result rows.

## Tech used

### Frontend

The interface uses JavaScript and JSX, with HTML for the entry page and CSS for the
layout. React state holds the messages, draft, and pending clarification. Native
`fetch` sends requests to the Python API.

| Technology | Version in package.json | What it does here |
| --- | --- | --- |
| React and React DOM | 19.3.0 | Render the chat and update it as messages arrive |
| Vite | 8.3.4 | Run the development server, proxy API requests, and build the frontend |
| @vitejs/plugin-react | 6.1.2 | Connect React to Vite's development and build tools |
| Tailwind CSS and @tailwindcss/vite | 4.3.3 | Style the UI components and compile Tailwind through Vite |
| shadcn/ui | Components copied into the project | Supply Button, Textarea, Collapsible, and Table components that can be edited locally |
| @radix-ui/react-collapsible | 1.2.1 | Handle the expandable SQL panel |
| @radix-ui/react-slot | 1.5.0 | Let component behavior attach to a child element through asChild |
| lucide-react | 1.57.0 | Provide the interface icons |
| class-variance-authority | 0.7.1 | Define button styles and sizes |
| clsx | 2.1.1 | Combine conditional CSS class names |
| tailwind-merge | 3.7.0 | Resolve conflicting Tailwind classes in the shared cn helper |

Node.js runs the frontend tools, and npm installs the packages. Dependencies are
pinned in `package.json` and `package-lock.json`. The UI uses React state directly,
without a separate router or state management library.

### Backend and database

Python handles the chat workflow, schema inspection, and query execution.

| Technology | Version in requirements.txt | What it does here |
| --- | --- | --- |
| FastAPI | 0.143.0 | Expose the chat and health endpoints and serve the compiled frontend |
| Uvicorn | 0.54.0 | Run the Python web server on localhost |
| Requests | 2.34.2 | Send HTTP requests to the local Ollama service |
| Psycopg 3 with binary support | 3.3.6 | Connect to PostgreSQL and execute queries |
| python-dotenv | 1.2.4 | Read configuration from the root .env file |
| SQLGlot | 30.22.0 | Parse SQL, resolve columns against the schema, enforce query restrictions, and add row limits |
| Pydantic | Installed through FastAPI | Validate request fields, message lengths, and conversation context |
| Supabase PostgreSQL | Hosted database | Store the synthetic dataset and execute SQL through the Session Pooler |

The PostgreSQL Session Pooler is used because it supports the project's connection
from an IPv4 network. There is no Supabase JavaScript client in the frontend;
Psycopg connects from Python using database credentials.

### Local model and tests

Ollama runs `qwen2.5:7b` on your computer. Python calls its `/api/chat` endpoint and
asks for structured JSON containing SQL, a clarification, or an unsupported-request
message. Model configuration is kept in `.env`.

The development requirements add pytest 9.1.1 and HTTPX 0.28.1. pytest runs the
backend tests, and HTTPX supports FastAPI's test client. Tests use mocked services
and synthetic schema metadata.

## How an answer is produced

For a database question, Python reads the live schema before asking the model to
write SQL. The prompt includes the question, column types, relationships, revenue
rules, and recent query context.

SQLGlot parses the candidate query and checks the permitted tables, columns, and
functions. The executor validates it again before opening a read-only database
transaction. Only after those checks does PostgreSQL run the query.

The API returns the executed SQL with its column names, rows, assumptions, and
execution time. React displays the answer and leaves the SQL panel collapsed until
you open it. Scalar results are shown directly; other results appear in a table.
Decimal values travel as strings to preserve their precision, and dates use ISO
format. Answers describe the rows returned by the database without a second model
call to summarize them.

A clarification pauses SQL execution. Your next message supplies the missing detail.
Submitting an answerable database question runs the validated query automatically;
there is no separate approval button.

## Run locally

The project uses Python 3.12 and a `.venv` environment. You also need Node.js, npm,
Ollama with `qwen2.5:7b` installed, and access to the Supabase dataset.

Run the commands from the project root in a VS Code PowerShell terminal. Your
existing `.env` stays in that directory and is read only by Python. On a fresh
checkout, create `.venv` and copy `.env.example` to `.env`, then fill in your
connection details privately. Start Ollama if it is not already running.

### Serve the built app

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Python serves both the compiled
React app and the API. Stop the server with Ctrl+C. Rebuild the frontend after
changing its source files, then restart Python to serve the updated build.

### Work on the frontend

Keep the Python server running in one terminal. In another terminal, run:

```powershell
cd frontend
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). Vite updates the page as you edit
React files and forwards `/api` requests to Python on port 8000. Both terminals
need to stay running for database questions to work.

If Vite reports that port 5173 is already in use, check the existing page first.
The frontend may already be running in another terminal. Stop that instance with
Ctrl+C before starting another one.

## Configuration

Use `.env.example` as the reference. Keep passwords in `.env`, which is excluded
by `.gitignore`; never put credentials in React source files.

| Variable | Default or expected value | Purpose |
| --- | --- | --- |
| DATABASE_URL | Your PostgreSQL Session Pooler connection URI | Database access; required |
| OLLAMA_URL | http://127.0.0.1:11434 | Local model service; only loopback HTTP addresses are accepted |
| OLLAMA_MODEL | qwen2.5:7b | Model used for SQL generation |
| MAX_ROWS | 200 | Maximum returned rows; allowed range is 1 to 1,000 |
| STATEMENT_TIMEOUT_MS | 10000 | PostgreSQL statement timeout; allowed range is 100 to 60,000 ms |
| MODEL_TIMEOUT_SECONDS | 180 | Model response timeout; allowed range is 10 to 600 seconds |

Copy the exact pooler host and username from your Supabase connection settings.
Use your database password, not a Supabase API key. Percent-encode reserved
characters in the password portion of the URI. Existing process environment
variables take precedence over values in `.env`. Restart Python after changing
configuration.

## Dataset and revenue rules

The app reads four ordinary tables in the `public` schema:

| Table | Contents |
| --- | --- |
| customers | Customer details, region, segment, and join date |
| products | Product names, categories, current prices, and active status |
| orders | Customer reference, order date, status, channel, and payment method |
| order_items | Order and product references, quantity, sale price, and discount |

Orders reference customers. Order items reference both orders and products. The
app retrieves the actual readable columns, types, and constraints from PostgreSQL
rather than relying on a fixed schema in its prompt.

Revenue uses completed orders and fractional discounts. In this dataset, 0.15 means
15%. The formula is `quantity * order_items.unit_price * (1-discount_percent)`.
For example, two items priced at 100 with a 0.15 discount produce 170 in revenue.
The price comes from the order item because that is the price paid for the sale.

These rules are fixed in the current frontend. They guide the model, so inspect the
SQL and assumptions to confirm that a particular answer applies them correctly.

## Project files

| File or directory | Purpose |
| --- | --- |
| server.py | Local chat API, health endpoint, and compiled frontend serving |
| frontend/src/App.jsx | Chat messages, result tables, SQL panel, CSV export, and profile links |
| frontend/src/main.jsx | React entry point |
| frontend/src/index.css | Layout, responsive styles, and theme |
| frontend/src/components/ui/ | Editable shadcn components |
| frontend/src/lib/utils.js | Shared class-name helper |
| frontend/vite.config.js | React and Tailwind plugins, aliases, and API proxy |
| frontend/components.json | shadcn component configuration |
| src/chat.py | Greetings, clarification context, and result formatting |
| src/config.py | Environment configuration and local endpoint restrictions |
| src/errors.py | Error messages safe to show in the chat |
| src/schema_inspector.py | Live columns, types, and relationships |
| src/ollama_client.py | Local model requests and timeouts |
| src/prompt_builder.py | Model instructions and schema-aware prompt |
| src/sql_generator.py | Structured model response parsing |
| src/sql_validator.py | Statement, function, table, and column checks |
| src/database.py | Read-only connections, SSL, and timeouts |
| src/query_executor.py | Revalidation and bounded query results |
| tests/ | Chat, API, configuration, prompt, and SQL safety tests |
| scripts/check_connections.py | Database and local-model diagnostics without printing secrets |
| docs/EVALUATION.md | Questions and guidance for checking answer correctness |

The API exposes `GET /api/health` for a basic server check and `POST /api/chat` for
messages. The frontend sends the `X-Chat-Client: ask-your-data` header along with
its JSON request. The health endpoint reports server availability, not database
or model connectivity.

## Privacy and query safety

Questions and schema metadata go to the local Ollama service. Query results do not
go back to the model. Supabase remains an external hosted database service, so
database operations use the network.

The parser rejects writes, multiple statements, unsafe functions, unsupported
constructs, and tables outside the inspected schema. Execution uses read-only
transactions, a statement timeout, a two-second lock timeout, and a row limit.
Application-supplied values in metadata and timeout queries are parameterized.
CSV exports neutralize spreadsheet formula prefixes in text cells, and SQL is
displayed as escaped text.

The model client disables environment proxies and redirects. The Python server
binds to loopback, checks browser origins and host headers, and requires the custom
header on POST requests. Those checks support local use; they are not authentication
for a public service. Database credentials stay on the backend, and the chat receives
sanitized errors rather than raw driver errors.

The connection requires SSL with `sslmode=require`. Full certificate and hostname
verification would need Supabase's CA and a `verify-full` connection policy in the
connection code. A dedicated database role with SELECT-only grants and appropriate
RLS policies is recommended before deployment, especially if the current credentials
use `postgres`.

The validator is designed for this known synthetic dataset. It cannot prove that a
query answers the intended question, and a row limit does not make every aggregation
cheap. A model can choose the wrong join, date range, or metric. Check its SQL when
an answer matters. General greetings use a small set of predefined replies; broader
conversation is outside the app's scope.

## Tests and answer checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_connections.py
```

The automated tests cover SQL restrictions, schema resolution, structured model
responses, local endpoint settings, chat behavior, and API request validation.
The connection script checks the real database and configured Ollama model without
printing passwords or result rows.

A passing test suite does not measure model accuracy. Use the questions in
[docs/EVALUATION.md](docs/EVALUATION.md) and compare answers against trusted SQL.
Record execution success separately from result correctness, and treat clarification
cases separately.

## Author

Harsh Gupta

[LinkedIn](https://www.linkedin.com/in/harsh-gupta-heytechie/) · [GitHub](https://github.com/heyharshu)

Reference documentation: [shadcn](https://ui.shadcn.com/docs/components),
[Vite](https://vite.dev/guide/), [FastAPI](https://fastapi.tiangolo.com/tutorial/).
