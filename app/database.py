"""Database engine and request-scoped session helpers."""

import os
from collections.abc import Generator

from fastapi import Request
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

DEFAULT_DATABASE_URL = "sqlite:///./stockpilot.db"


def make_engine(database_url: str | None = None) -> Engine:
    """Create an engine for the configured URL or the local SQLite database."""
    url = database_url or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build sessions that do not leak state between requests."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def initialize_database(engine: Engine) -> None:
    """Create any missing tables when an application instance starts."""
    Base.metadata.create_all(bind=engine)


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a session bound to this application's configured database."""
    session_factory = request.app.state.session_factory
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
