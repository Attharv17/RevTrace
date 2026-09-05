from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import get_settings

settings = get_settings()

# SQLite requires check_same_thread=False; PostgreSQL does not need this.
_connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# Alias used by Phase 3+ API modules
get_session = get_db
