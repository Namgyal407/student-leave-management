"""Database connection module using SQLAlchemy."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://leave_app:leave_app_password@localhost:5432/leave_management"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Return the SQLAlchemy session bound to the current Flask request."""
    from flask import g
    if "db" not in g:
        g.db = SessionLocal()
    return g.db


def close_session(exc=None):
    """Flask teardown hook: roll back on error and always close the session."""
    from flask import g
    session = g.pop("db", None)
    if session is not None:
        if exc is not None:
            session.rollback()
        session.close()
