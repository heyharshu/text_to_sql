# Local Text-to-SQL sample dataset for Supabase

All records are synthetic and for learning/portfolio use.

## Files
- `customers.csv`: 100 customers
- `products.csv`: 20 products
- `orders.csv`: 450 orders
- `order_items.csv`: order line items

## Import
1. In Supabase SQL Editor, run `schema.sql`.
2. In Table Editor, import each CSV into its matching table.
3. Import in foreign-key order: customers → products → orders → order_items.

## Example questions
- Which 10 customers generated the highest revenue in the last 6 months?
- Which products sold the most units?
- Compare revenue by region.
- What is the average order value by sales channel?
- Which category has the highest revenue?
- Which customers placed more than five completed orders?

Revenue formula: `quantity * unit_price * (1 - discount_percent)`.
For revenue analyses, decide whether to include only `completed` orders; the examples should generally do so.

## Privacy and security
Ollama inference can remain local. Supabase is a hosted database, so your app's SQL requests and database responses will travel to Supabase; they do not need to be sent to a cloud LLM. Keep credentials server-side, use least-privilege access, and never commit secrets to Git.
