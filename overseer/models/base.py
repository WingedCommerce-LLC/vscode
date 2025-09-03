"""
Base Database Model

This module contains the base model class that all other models inherit from.
Provides common fields like id, created_at, and updated_at.
"""

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model that provides common fields for all database models.

    Fields:
        id: UUID primary key
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
