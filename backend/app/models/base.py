"""Shared SQLAlchemy base + helpers."""
import uuid
from sqlalchemy.orm import DeclarativeBase


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass
