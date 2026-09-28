"""Inventory operations that keep stock and its transaction log consistent."""

from decimal import Decimal

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Product, Transaction


class DuplicateSKUError(ValueError):
    """Raised when a product uses an SKU already present in the database."""


class ProductNotFoundError(LookupError):
    """Raised when an operation refers to a product that does not exist."""


class InsufficientStockError(ValueError):
    """Raised when a sale exceeds the product's available stock."""


class InvalidQuantityError(ValueError):
    """Raised when an inventory operation has a non-positive quantity."""


def create_product(
    db: Session,
    *,
    name: str,
    sku: str,
    quantity: int,
    price: Decimal,
    low_stock_threshold: int,
) -> Product:
    """Create a product, translating unique constraint errors to a domain error."""
    product = Product(
        name=name.strip(),
        sku=sku.strip().upper(),
        quantity=quantity,
        price=price,
        low_stock_threshold=low_stock_threshold,
    )
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "sku" in str(exc).lower() or "unique" in str(exc).lower():
            raise DuplicateSKUError from exc
        raise
    db.refresh(product)
    return product


def sell_product(db: Session, product_id: int, quantity: int) -> Product:
    """Atomically lower stock and record a sale if enough units are available."""
    if quantity <= 0:
        raise InvalidQuantityError
    product = db.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError

    result = db.execute(
        update(Product)
        .where(Product.id == product_id, Product.quantity >= quantity)
        .values(quantity=Product.quantity - quantity)
    )
    if result.rowcount != 1:
        db.rollback()
        raise InsufficientStockError

    db.add(Transaction(product_id=product_id, type="sale", quantity=quantity))
    db.commit()
    db.refresh(product)
    return product


def restock_product(db: Session, product_id: int, quantity: int) -> Product:
    """Increase stock and record a restock in one database transaction."""
    if quantity <= 0:
        raise InvalidQuantityError
    product = db.get(Product, product_id)
    if product is None:
        raise ProductNotFoundError

    product.quantity += quantity
    db.add(Transaction(product_id=product_id, type="restock", quantity=quantity))
    db.commit()
    db.refresh(product)
    return product
