"""SQLAlchemy models for products and their stock transactions."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class shared by all ORM models."""


class Product(Base):
    """An item tracked in the inventory."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_products_nonnegative_quantity"),
        CheckConstraint("price >= 0", name="ck_products_nonnegative_price"),
        CheckConstraint(
            "low_stock_threshold >= 0", name="ck_products_nonnegative_threshold"
        ),
        Index("ix_products_sku", "sku", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sku: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Transaction(Base):
    """A recorded sale or restock for a product."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('sale', 'restock')", name="ck_transactions_type"),
        CheckConstraint("quantity > 0", name="ck_transactions_positive_quantity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    product: Mapped[Product] = relationship(back_populates="transactions")
