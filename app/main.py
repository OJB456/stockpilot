"""FastAPI entry point and browser routes for StockPilot."""

import os
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db, initialize_database, make_engine, make_session_factory
from app.models import Product, Transaction
from app.services import (
    DuplicateSKUError,
    InsufficientStockError,
    InvalidQuantityError,
    ProductNotFoundError,
    create_product,
    restock_product,
    sell_product,
)

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def get_commit() -> str:
    """Return the commit supplied by CI or Render, with a local-dev fallback."""
    return (
        os.getenv("GIT_COMMIT", "").strip()
        or os.getenv("RENDER_GIT_COMMIT", "").strip()
        or "local-dev"
    )


def _render(
    request: Request, template_name: str, *, status_code: int = 200, **context
) -> HTMLResponse:
    """Render a page and consistently expose the running commit in its footer."""
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"commit": get_commit(), **context},
        status_code=status_code,
    )


def _dashboard_redirect(*, message: str | None = None, error: str | None = None):
    """Return a post/redirect/get response with a short user-facing result."""
    parts = []
    if message:
        parts.append(f"message={quote(message, safe='')}")
    if error:
        parts.append(f"error={quote(error, safe='')}")
    suffix = f"?{'&'.join(parts)}" if parts else ""
    return RedirectResponse(url=f"/{suffix}", status_code=303)


def _integer(value: str, label: str, *, minimum: int) -> tuple[int | None, str | None]:
    """Parse an integer form value and enforce its lower bound."""
    try:
        number = int(value.strip())
    except (AttributeError, ValueError):
        return None, f"{label} must be a whole number."
    if number < minimum:
        if minimum == 1:
            return None, f"{label} must be greater than zero."
        return None, f"{label} cannot be negative."
    return number, None


def _quantity_from_form(value: str) -> tuple[int | None, str | None]:
    """Validate positive quantities used for sales and restocks."""
    return _integer(value, "Quantity", minimum=1)


def create_app(database_url: str | None = None) -> FastAPI:
    """Create an app instance; tests can supply their own isolated database URL."""
    engine = make_engine(database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        initialize_database(engine)
        yield
        engine.dispose()

    app = FastAPI(title="StockPilot", version="1.0.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

    @app.get("/", response_class=HTMLResponse, name="dashboard")
    def dashboard(
        request: Request,
        message: str | None = None,
        error: str | None = None,
        db: Session = Depends(get_db),
    ):
        products = db.scalars(select(Product).order_by(Product.name, Product.id)).all()
        total_products = len(products)
        total_units = sum(product.quantity for product in products)
        inventory_value = sum(
            (product.price * product.quantity for product in products), Decimal("0.00")
        )
        low_stock_count = sum(
            1
            for product in products
            if product.quantity > 0 and product.quantity < product.low_stock_threshold
        )
        return _render(
            request,
            "index.html",
            products=products,
            total_products=total_products,
            total_units=total_units,
            inventory_value=inventory_value,
            low_stock_count=low_stock_count,
            message=message,
            error=error,
        )

    @app.get("/add", response_class=HTMLResponse, name="add_product_form")
    def add_product_form(request: Request):
        return _render(request, "add_product.html", values={}, error=None)

    @app.post("/add", response_class=HTMLResponse, name="add_product")
    def add_product(
        request: Request,
        name: str = Form(default=""),
        sku: str = Form(default=""),
        quantity_value: str = Form(default="", alias="quantity"),
        price_value: str = Form(default="", alias="price"),
        threshold_value: str = Form(default="", alias="low_stock_threshold"),
        db: Session = Depends(get_db),
    ):
        values = {
            "name": name,
            "sku": sku,
            "quantity": quantity_value,
            "price": price_value,
            "low_stock_threshold": threshold_value,
        }
        clean_name = name.strip()
        clean_sku = sku.strip().upper()
        if not clean_name:
            error = "Product name cannot be empty."
        elif len(clean_name) > 120:
            error = "Product name must be 120 characters or fewer."
        elif not clean_sku:
            error = "SKU cannot be empty."
        elif len(clean_sku) > 40:
            error = "SKU must be 40 characters or fewer."
        else:
            quantity, error = _integer(quantity_value, "Initial quantity", minimum=0)
            if error:
                return _render(request, "add_product.html", values=values, error=error)
            threshold, error = _integer(threshold_value, "Low-stock threshold", minimum=0)
            if error:
                return _render(request, "add_product.html", values=values, error=error)
            try:
                price = Decimal(price_value.strip())
                if not price.is_finite() or price < 0:
                    raise InvalidOperation
                if price.as_tuple().exponent < -2:
                    error = "Price can have at most two decimal places."
            except (AttributeError, InvalidOperation, ValueError):
                error = "Price must be a valid amount that is zero or greater."
                price = Decimal("0.00")
            if error:
                return _render(request, "add_product.html", values=values, error=error)

        if error:
            return _render(request, "add_product.html", values=values, error=error)

        try:
            product = create_product(
                db,
                name=clean_name,
                sku=clean_sku,
                quantity=quantity,
                price=price,
                low_stock_threshold=threshold,
            )
        except DuplicateSKUError:
            return _render(
                request,
                "add_product.html",
                values=values,
                error=f"SKU {clean_sku} is already in use. Choose a unique SKU.",
                status_code=409,
            )
        except SQLAlchemyError:
            db.rollback()
            return _render(
                request,
                "add_product.html",
                values=values,
                error="The product could not be saved because of a database error. Try again.",
                status_code=500,
            )
        return _dashboard_redirect(message=f"{product.name} was added to your inventory.")

    @app.post("/sell/{product_id}", name="sell")
    def sell(
        product_id: int,
        quantity_value: str = Form(default="", alias="quantity"),
        db: Session = Depends(get_db),
    ):
        quantity, error = _quantity_from_form(quantity_value)
        if error:
            return _dashboard_redirect(error=error)
        try:
            product = sell_product(db, product_id, quantity)
        except ProductNotFoundError:
            return _dashboard_redirect(error="That product no longer exists.")
        except InsufficientStockError:
            return _dashboard_redirect(error="There is not enough stock to complete that sale.")
        except InvalidQuantityError:
            return _dashboard_redirect(error="Quantity must be greater than zero.")
        except SQLAlchemyError:
            db.rollback()
            return _dashboard_redirect(
                error="The sale could not be saved because of a database error."
            )
        return _dashboard_redirect(message=f"Sold {quantity} {product.name}.")

    @app.post("/restock/{product_id}", name="restock")
    def restock(
        product_id: int,
        quantity_value: str = Form(default="", alias="quantity"),
        db: Session = Depends(get_db),
    ):
        quantity, error = _quantity_from_form(quantity_value)
        if error:
            return _dashboard_redirect(error=error)
        try:
            product = restock_product(db, product_id, quantity)
        except ProductNotFoundError:
            return _dashboard_redirect(error="That product no longer exists.")
        except InvalidQuantityError:
            return _dashboard_redirect(error="Quantity must be greater than zero.")
        except SQLAlchemyError:
            db.rollback()
            return _dashboard_redirect(
                error="The restock could not be saved because of a database error."
            )
        return _dashboard_redirect(message=f"Restocked {quantity} {product.name}.")

    @app.get("/history", response_class=HTMLResponse, name="history")
    def history(request: Request, db: Session = Depends(get_db)):
        rows = db.execute(
            select(Transaction, Product)
            .join(Product, Transaction.product_id == Product.id)
            .order_by(Transaction.timestamp.desc(), Transaction.id.desc())
        ).all()
        return _render(request, "history.html", transactions=rows)

    @app.get("/health", name="health")
    def health():
        return JSONResponse({"status": "ok", "commit": get_commit()})

    @app.exception_handler(404)
    async def not_found(request: Request, _exc: HTTPException):
        return _render(request, "404.html", status_code=404)

    return app


app = create_app()
