from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# Async Engine (for FastAPI)
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "server_settings": {
            "statement_timeout": "3000", 
            "idle_in_transaction_session_timeout": "60000",
        }
    }
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync Engine (for Alembic migrations and background tasks)
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    future=True,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# Dependency Injection Functions
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Generator[Session, None, None]:
    db = SyncSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# TODO: Add Redis caching layer for frequently accessed data
# TODO: Add read replica routing for read-heavy operations
# TODO: Add connection health checks and circuit breaker pattern
# TODO: Implement database query metrics collection

# Future Enhancements:
    # - Add connection pooling optimization
    # - Add read replica support
    # - Add query caching with Redis
    # - Add database sharding for multi-tenancy

