"""Declarative base class.

All ORM models inherit from this; single import point for Alembic autogeneration.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all Forge ORM models."""

    pass
