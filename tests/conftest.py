import pytest

@pytest.fixture
def schema():
    def cols(**types):
        return {name: {"type": kind, "nullable": False} for name, kind in types.items()}
    return {"schema": "public", "tables": {
        "customers": cols(customer_id="integer", customer_name="text", region="text", joined_at="date"),
        "products": cols(product_id="integer", product_name="text", category="text", unit_price="numeric(12,2)", active="boolean"),
        "orders": cols(order_id="integer", customer_id="integer", order_date="date", status="text"),
        "order_items": cols(order_item_id="integer", order_id="integer", product_id="integer", quantity="integer", unit_price="numeric(12,2)", discount_percent="numeric(4,2)"),
    }, "constraints": []}
