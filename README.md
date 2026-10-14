# Ask your data

A Text-to-SQL chat app by Harsh Gupta that lets you explore an e-commerce database
by asking questions in plain English. Each database answer includes a result table
or a single value, with a **View SQL** option to inspect the query that produced it.

## Why this project matters

Managers and other nontechnical users often know what they want to ask but do not
know how to write SQL. This app gives them a way to query the connected database
through a chat box. A sales manager can type "Which products earned the most revenue?"
or "Compare revenue by region" and see the results without opening a database tool
or writing a query themselves.

That can make routine reporting easier and reduce the need to ask a developer or
analyst for every small data question. These are intended benefits, not measured
time savings. The included synthetic dataset makes it possible to demonstrate the
workflow without using real customer records.

Database access still goes through the Python backend and its configured permissions.
The app provides a plain-English interface to read data; it does not give users
database credentials or unrestricted access. For a team deployment, authentication
and permissions would need to be configured for the intended users.

React handles the interface. Python inspects the live schema, asks local Qwen for
SQL, validates it, and runs a read-only query against Supabase. No external LLM is
used. General greetings are handled locally without a database request.

## Run

Your existing .env stays in the project root. It is used only by Python and is
never copied into the frontend. Node.js and the existing Python virtual environment
are needed.

First, in PowerShell from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe server.py
```

Open http://127.0.0.1:8000. This serves both the compiled React app and API with one
Python process. Stop with Ctrl+C. Start Ollama if it is not already running.

For frontend development, run the Python server in one terminal, then:

```powershell
cd frontend
npm run dev
```

Open http://127.0.0.1:5173. Vite forwards /api requests to the Python server. There
is no frontend database password, API key, or separate CORS setup.

## Using the chat

- Try `hi`, `hlo`, or `how are you`.
- Ask `How many orders do we have by status?`.
- Open **View SQL** under the response to inspect or copy the executed query.
- Follow up with a filter or another related question. The last four executed
  questions and queries provide context; result rows do not go back to the model.
- If a question needs clarification, answer it in the next message.
- Refresh the page to start a new conversation. Nothing is saved to local storage.
- Result tables have a CSV download. SQL is escaped as plain text, never rendered
  as HTML. Spreadsheet formula prefixes in exported text are neutralized.

The supplied schema stores discounts as fractions: 0.15 means 15%. Revenue defaults
to completed orders and uses `quantity * order_items.unit_price * (1-discount_percent)`.
Order item prices reflect the sale, rather than the current product price.

## Included dataset

The sample data is included in [text_to_sql_supabase_dataset/](text_to_sql_supabase_dataset/).
All records are synthetic and intended for learning and portfolio demonstrations.
The CSVs contain 100 customers, 20 products, 450 orders, and 1,129 order items.

| File | What it contains |
| --- | --- |
| [schema.sql](text_to_sql_supabase_dataset/schema.sql) | Table definitions, primary keys, foreign keys, and value constraints |
| [customers.csv](text_to_sql_supabase_dataset/customers.csv) | Customer names, regions, segments, and join dates |
| [products.csv](text_to_sql_supabase_dataset/products.csv) | Products, categories, prices, and active status |
| [orders.csv](text_to_sql_supabase_dataset/orders.csv) | Orders with dates, customers, statuses, sales channels, and payment methods |
| [order_items.csv](text_to_sql_supabase_dataset/order_items.csv) | Individual order lines with quantities, sale prices, and fractional discounts |
| [Dataset README](text_to_sql_supabase_dataset/README.md) | Import instructions and sample questions |

On a new database, run `text_to_sql_supabase_dataset/schema.sql` in the Supabase SQL
Editor, then import each CSV into its matching table through the Table Editor.
Import in this order: customers, products, orders, then order_items. The order matters
because orders reference customers, and order items reference orders and products.
Skip this setup if you already imported the dataset.

Keeping the CSVs in the repository does not load them into the app automatically.
Answers come from the connected PostgreSQL database. The backend inspects its live
schema before generating SQL.

Try questions such as "Which products sold the most units?", "What is the average
order value by sales channel?", or "Which customers placed more than five completed
orders?". If a question leaves out an essential date range or metric, the model is
prompted to ask for clarification.

## Files worth reading

| File | Purpose |
| --- | --- |
| server.py | Two local API routes and serving the compiled React app |
| frontend/src/App.jsx | Chat, messages, result table, SQL toggle, profile links |
| frontend/src/index.css | Small layout and theme stylesheet |
| frontend/src/components/ui/ | Actual shadcn components added from its registry |
| src/chat.py | Greetings, clarification context, database answers |
| src/schema_inspector.py | Real columns, types, and relationships |
| src/ollama_client.py | Local model requests and timeouts |
| src/prompt_builder.py | Model instructions and schema-aware prompt |
| src/sql_generator.py | Structured SQL/clarification response parsing |
| src/sql_validator.py | Allowed statements, functions, tables, and columns |
| src/database.py | Read-only connection, SSL, and timeouts |
| src/query_executor.py | Revalidation and bounded query results |
| tests/ | SQL safety, model handling, chat, and API tests |
| scripts/check_connections.py | Safe database and local-model diagnostics |
| text_to_sql_supabase_dataset/ | Synthetic CSV data, SQL schema, and import instructions |

## Technologies and their roles

| Technology | Role in the project |
| --- | --- |
| React and React DOM | Render the chat and update messages and results |
| JavaScript, JSX, HTML, and CSS | Define the interface, interactions, page entry point, and responsive layout |
| Vite and @vitejs/plugin-react | Run frontend development, proxy API calls to Python, and build the app |
| Tailwind CSS and @tailwindcss/vite | Style the components and compile the utility classes |
| shadcn/ui | Provide editable Button, Textarea, Collapsible, and Table components |
| Radix Collapsible and Slot | Handle the expandable SQL panel and component composition |
| lucide-react | Supply interface icons |
| class-variance-authority | Define button variants and sizes |
| clsx and tailwind-merge | Combine CSS class names and resolve conflicting Tailwind classes |
| Node.js and npm | Run frontend tools and manage JavaScript dependencies |
| Python | Coordinate schema inspection, model requests, SQL validation, and database answers |
| FastAPI and Pydantic | Expose the chat API and validate request fields and lengths |
| Uvicorn | Serve the Python API and compiled frontend on localhost |
| Ollama and qwen2.5:7b | Run the language model locally and generate candidate SQL from questions |
| Requests | Send prompts to the local Ollama HTTP API |
| Supabase PostgreSQL | Store the dataset and execute SQL through the Session Pooler |
| Psycopg 3 | Connect Python to PostgreSQL and fetch query results |
| python-dotenv | Load configuration and database credentials from .env |
| SQLGlot | Parse SQL, check schema references and allowed constructs, and apply row limits |
| pytest and HTTPX | Test SQL safety, chat handling, and API behavior with mocked services |

The chat uses React state and native `fetch` for API requests. shadcn components
live in the repository and can be edited directly. Exact dependency versions are
recorded in `frontend/package.json`, `frontend/package-lock.json`, and the Python
requirements files.

## Safety and limitations

Submitting a database question now runs the validated read-only query directly,
then displays its SQL alongside the answer. It does not wait for a separate
approval click. The executor still rejects multiple statements, writes, unsafe
functions, unsupported constructs, and tables outside the inspected schema.
Every operation uses read-only transactions, timeouts, and a result limit.

Qwen and questions stay local. Supabase remains an external hosted database service.
The local API binds to loopback, rejects foreign browser origins, and requires a
custom header on POST requests. These are local-browser safeguards, not public
hosting authentication. Do not expose the development servers to the internet.
Database credentials stay in .env. No raw driver errors are returned to the chat.

The current credentials may use the powerful postgres role. A dedicated SELECT-only
role with appropriate RLS policies is recommended before deployment. SSL is required;
full certificate verification needs Supabase's CA and a verify-full connection policy.
The validator is intended for your known synthetic dataset, not arbitrary databases.

Answers describe the actual returned rows, with scalar values shown directly and
larger results in tables. The model may still choose the wrong interpretation, so
check the SQL and assumptions. Generic greetings use simple local responses; this
is not an unrestricted general-purpose chatbot.

## Check it

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\check_connections.py
```

Tests use mocked services and synthetic metadata. See docs/EVALUATION.md for questions
to compare against trusted SQL. Backend safety tests do not measure model accuracy.
Frontend dependencies are pinned in package.json and package-lock.json. Use npm ci
for repeatable installation.

## Author

Harsh Gupta

[LinkedIn](https://www.linkedin.com/in/harsh-gupta-heytechie/) · [GitHub](https://github.com/heyharshu)

References: [shadcn](https://ui.shadcn.com/docs/components),
[Vite](https://vite.dev/guide/), [FastAPI](https://fastapi.tiangolo.com/tutorial/).
