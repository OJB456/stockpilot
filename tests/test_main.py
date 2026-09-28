"""Behavior-focused route and persistence tests using an isolated SQLite file."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import create_app
from app.models import Product, Transaction


@pytest.fixture
def client(tmp_path):
    """Give each test an application backed by its own temporary database."""
    database_file = tmp_path / "stockpilot-test.db"
    app = create_app(f"sqlite:///{database_file.as_posix()}")
    with TestClient(app) as test_client:
        yield test_client


def add_product(
    client,
    *,
    name="Wireless keyboard",
    sku="KEY-001",
    quantity="10",
    price="39.99",
    threshold="3",
):
    """Create a product using the same form fields a browser sends."""
    return client.post(
        "/add",
        data={
            "name": name,
            "sku": sku,
            "quantity": quantity,
            "price": price,
            "low_stock_threshold": threshold,
        },
        follow_redirects=True,
    )


def product_state(client, sku="KEY-001"):
    """Read persisted state from the test application's temporary database."""
    with client.app.state.session_factory() as db:
        product = db.scalar(select(Product).where(Product.sku == sku))
        if product is None:
            return None, []
        transactions = db.scalars(
            select(Transaction).where(Transaction.product_id == product.id)
        ).all()
        return product, transactions


def test_health_endpoint_reports_commit_from_environment(client, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "abc123")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "render456")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "commit": "abc123"}


def test_health_endpoint_falls_back_to_render_commit_and_local_dev(client, monkeypatch):
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "render456")
    assert client.get("/health").json()["commit"] == "render456"

    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    assert client.get("/health").json()["commit"] == "local-dev"


def test_adding_product_persists_normalized_values_and_redirects(client):
    response = add_product(client, name="  Wireless keyboard  ", sku=" key-001 ")

    assert response.status_code == 200
    assert "Wireless keyboard was added" in response.text
    product, transactions = product_state(client)
    assert product.name == "Wireless keyboard"
    assert product.sku == "KEY-001"
    assert product.quantity == 10
    assert product.price == Decimal("39.99")
    assert product.low_stock_threshold == 3
    assert transactions == []


def test_product_appears_on_dashboard_with_inventory_totals(client):
    add_product(client, quantity="4", price="12.50")

    response = client.get("/")

    assert "Wireless keyboard" in response.text
    assert "KEY-001" in response.text
    assert "$50.00" in response.text
    assert "Stock units" in response.text
    assert "In stock" in response.text


def test_duplicate_sku_is_rejected_case_insensitively(client):
    add_product(client)

    response = client.post(
        "/add",
        data={
            "name": "Second keyboard",
            "sku": " key-001 ",
            "quantity": "2",
            "price": "10.00",
            "low_stock_threshold": "1",
        },
    )

    assert response.status_code == 409
    assert "SKU KEY-001 is already in use" in response.text
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count(Product.id))) == 1


def test_sale_reduces_stock_and_records_sale_transaction(client):
    add_product(client)

    response = client.post("/sell/1", data={"quantity": "3"}, follow_redirects=True)

    assert "Sold 3 Wireless keyboard" in response.text
    product, transactions = product_state(client)
    assert product.quantity == 8
    assert [(item.type, item.quantity) for item in transactions] == [("sale", 3)]


def test_insufficient_stock_keeps_stock_and_transaction_log_unchanged(client):
    add_product(client, quantity="10")

    response = client.post("/sell/1", data={"quantity": "11"}, follow_redirects=True)

    assert "not enough stock" in response.text
    product, transactions = product_state(client)
    assert product.quantity == 10
    assert transactions == []


def test_stock_never_becomes_negative_after_rejected_sale(client):
    add_product(client, quantity="2")

    client.post("/sell/1", data={"quantity": "20"})

    product, transactions = product_state(client)
    assert product.quantity >= 0
    assert product.quantity == 2
    assert transactions == []


def test_restock_increases_stock_and_records_transaction(client):
    add_product(client, quantity="7")

    response = client.post("/restock/1", data={"quantity": "5"}, follow_redirects=True)

    assert "Restocked 5 Wireless keyboard" in response.text
    product, transactions = product_state(client)
    assert product.quantity == 12
    assert [(item.type, item.quantity) for item in transactions] == [("restock", 5)]


def test_history_shows_actual_sale_and_restock_rows_newest_first(client):
    add_product(client)
    client.post("/sell/1", data={"quantity": "1"})
    client.post("/restock/1", data={"quantity": "2"})

    response = client.get("/history")

    assert response.status_code == 200
    assert "Wireless keyboard" in response.text
    assert "KEY-001" in response.text
    assert response.text.index("Restock") < response.text.index("Sale")
    assert "+2" in response.text
    assert "−1" in response.text


def test_low_stock_and_out_of_stock_statuses_are_distinct(client):
    add_product(client, name="Almost gone", sku="LOW-001", quantity="2", threshold="3")
    add_product(client, name="Sold out", sku="OUT-001", quantity="0", threshold="5")

    response = client.get("/")

    assert "Almost gone" in response.text
    assert "Sold out" in response.text
    assert "Low stock" in response.text
    assert "Out of stock" in response.text
    assert 'class="stat-value">1</p>' in response.text


@pytest.mark.parametrize("quantity", ["0", "-1", "abc", "1.5", ""])
def test_invalid_sale_quantity_does_not_change_stock_or_log(quantity, client):
    add_product(client)

    response = client.post("/sell/1", data={"quantity": quantity}, follow_redirects=True)

    assert "Quantity" in response.text
    product, transactions = product_state(client)
    assert product.quantity == 10
    assert transactions == []


@pytest.mark.parametrize("quantity", ["0", "-1", "abc", "1.5", ""])
def test_invalid_restock_quantity_does_not_change_stock_or_log(quantity, client):
    add_product(client)

    response = client.post("/restock/1", data={"quantity": quantity}, follow_redirects=True)

    assert "Quantity" in response.text
    product, transactions = product_state(client)
    assert product.quantity == 10
    assert transactions == []


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"name": "   "}, "Product name cannot be empty"),
        ({"sku": "   "}, "SKU cannot be empty"),
        ({"quantity": "-1"}, "Initial quantity cannot be negative"),
        ({"price": "-1.00"}, "Price must be a valid amount"),
        ({"low_stock_threshold": "-1"}, "Low-stock threshold cannot be negative"),
    ],
)
def test_invalid_product_fields_are_explained_and_not_saved(overrides, message, client):
    form = {
        "name": "Wireless keyboard",
        "sku": "KEY-001",
        "quantity": "10",
        "price": "39.99",
        "low_stock_threshold": "3",
    }
    form.update(overrides)

    response = client.post("/add", data=form)

    assert response.status_code == 200
    assert message in response.text
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count(Product.id))) == 0


def test_missing_product_action_is_a_user_facing_error(client):
    response = client.post("/sell/999", data={"quantity": "1"}, follow_redirects=True)

    assert "That product no longer exists" in response.text


def test_unknown_page_uses_custom_404_template(client):
    response = client.get("/this-page-does-not-exist")

    assert response.status_code == 404
    assert "Looks like this page" in response.text
