-- Synthetic e-commerce schema for Supabase PostgreSQL.
-- Create tables first, then import CSVs in this order:
-- customers.csv, products.csv, orders.csv, order_items.csv.

create table if not exists public.customers (
  customer_id integer primary key,
  customer_name text not null,
  email text unique not null,
  region text not null,
  segment text not null,
  joined_at date not null
);

create table if not exists public.products (
  product_id integer primary key,
  product_name text not null,
  category text not null,
  unit_price numeric(12,2) not null check (unit_price >= 0),
  active boolean not null default true
);

create table if not exists public.orders (
  order_id integer primary key,
  customer_id integer not null references public.customers(customer_id),
  order_date date not null,
  status text not null check (status in ('completed','processing','cancelled','returned')),
  sales_channel text not null,
  payment_method text not null
);

create table if not exists public.order_items (
  order_item_id integer primary key,
  order_id integer not null references public.orders(order_id),
  product_id integer not null references public.products(product_id),
  quantity integer not null check (quantity > 0),
  unit_price numeric(12,2) not null check (unit_price >= 0),
  discount_percent numeric(4,2) not null default 0
    check (discount_percent >= 0 and discount_percent <= 1)
);
