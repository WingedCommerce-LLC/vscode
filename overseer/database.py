"""Database configuration and connection management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models.base import Base

# Database URL from environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://overseer:overseer_dev_password@postgres:5432/overseer'
)

# Convert to async URL if needed
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine with connection pooling
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=os.getenv('OVERSEER_ENV') == 'development'
)

# Create sync engine for migrations and setup
sync_engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=os.getenv('OVERSEER_ENV') == 'development'
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Create sync session factory (for migrations)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def get_async_db():
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_db():
    """Get synchronous database session (for migrations)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def create_tables_sync():
    """Create all database tables synchronously (for migrations)."""
    Base.metadata.create_all(bind=sync_engine)


def drop_tables_sync():
    """Drop all database tables synchronously (for migrations)."""
    Base.metadata.drop_all(bind=sync_engine)
