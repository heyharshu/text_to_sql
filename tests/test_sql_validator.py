import pytest
from src.errors import AppError
from src.sql_validator import validate_sql

@pytest.mark.parametrize("sql", [
    "SELECT customer_name FROM customers ORDER BY customer_name LIMIT 10",
    "SELECT region, COUNT(*) AS count FROM customers GROUP BY region",
    "SELECT p.product_name, SUM(i.quantity*i.unit_price*(1-i.discount_percent)) AS revenue FROM products p JOIN order_items i ON p.product_id=i.product_id JOIN orders o ON o.order_id=i.order_id WHERE o.status='completed' GROUP BY p.product_name ORDER BY revenue DESC LIMIT 10",
    "WITH totals AS (SELECT customer_id, COUNT(*) AS n FROM orders GROUP BY customer_id) SELECT c.customer_name, t.n FROM customers c JOIN totals t ON c.customer_id=t.customer_id",
    "SELECT DATE_TRUNC('month', order_date) AS month, COUNT(*) FROM orders WHERE order_date >= DATE '2025-01-01' AND order_date < DATE '2026-01-01' GROUP BY 1",
    "SELECT * FROM customers WHERE joined_at >= CURRENT_DATE - INTERVAL '30 days'",
    "SELECT customer_id FROM customers UNION ALL SELECT customer_id FROM orders",
    "SELECT customer_id, ROW_NUMBER() OVER (ORDER BY customer_id) FROM customers",
    "SELECT c.customer_name FROM customers c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id=c.customer_id)",
    "SELECT CASE WHEN active THEN 'Active' ELSE 'Inactive' END AS state FROM products",
    "SELECT ROUND(AVG(unit_price), 2), COALESCE(MIN(unit_price), 0) FROM products",
    "SELECT COUNT(*) FROM orders WHERE status IN ('completed','returned')",
    "SELECT 'DROP TABLE orders; --' AS label FROM orders",
])
def test_accepts_analytics(sql, schema):
    validated = validate_sql(sql, schema)
    assert "LIMIT" in validated
    assert validate_sql(validated, schema) == validated

@pytest.mark.parametrize("sql", [
    "DELETE FROM orders", "INSERT INTO orders VALUES (1)", "UPDATE products SET active=false",
    "DROP TABLE products", "ALTER TABLE customers ADD COLUMN x text", "TRUNCATE orders",
    "SELECT * FROM orders; SELECT * FROM products", "SELECT * FROM orders; DELETE FROM orders",
    "WITH erased AS (DELETE FROM orders RETURNING *) SELECT * FROM erased",
    "SELECT * INTO stolen FROM customers", "SELECT * FROM orders FOR UPDATE",
    "COPY customers TO '/tmp/out'", "SELECT pg_sleep(5) FROM orders",
    "SELECT pg_read_file('/etc/passwd') FROM orders", "SELECT set_config('transaction_read_only','off',false) FROM orders",
    "SELECT nextval('seq') FROM orders", "SELECT public.custom_function(customer_id) FROM customers",
    "SELECT * FROM pg_catalog.pg_class", "SELECT * FROM information_schema.tables",
    "SELECT * FROM private.customers", "SELECT * FROM other.public.customers",
    "SELECT * FROM generate_series(1,10000000)", "SELECT * FROM customers CROSS JOIN orders",
    "SELECT * FROM customers NATURAL JOIN orders", "SELECT missing_column FROM customers",
    "SELECT customer_id FROM customers c JOIN orders o ON c.customer_id=o.customer_id",
    "SELECT customer_id::regclass FROM customers", "SELECT customer_id::my_type FROM customers",
    "WITH RECURSIVE x AS (SELECT customer_id FROM customers UNION ALL SELECT customer_id FROM x) SELECT * FROM x",
    "SELECT * FROM orders LIMIT -1", "SELECT * FROM orders LIMIT ALL", "SELECT * FROM orders LIMIT 0",
    "SELECT 1", "", "SELEC * FROM orders", "SELECT * FROM unknown",
    "SELECT * FROM orders TABLESAMPLE SYSTEM (10)",
    "WITH secrets AS (SELECT * FROM customers) SELECT * FROM public.secrets",
])
def test_rejects_unsafe_or_invalid_sql(sql, schema):
    with pytest.raises(AppError):
        validate_sql(sql, schema)

def test_caps_large_limit(schema):
    assert validate_sql("SELECT * FROM orders LIMIT 100000", schema).endswith("LIMIT 200")

def test_keeps_smaller_limit(schema):
    assert validate_sql("SELECT * FROM orders LIMIT 7", schema).endswith("LIMIT 7")
