"""
Database - PostgreSQL database connection and operations
"""

from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Database:
    """
    Database connection manager using SQLAlchemy async.
    
    Provides:
    - Connection pooling
    - Session management
    - Migration support
    """
    
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection URL
            echo: Whether to log SQL statements
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        # Convert postgres:// to postgresql+asyncpg://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # asyncpg doesn't accept sslmode as a URL param — strip it and pass ssl=True via connect_args
        connect_args = {}
        if "sslmode=require" in database_url:
            database_url = database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
            connect_args["ssl"] = "require"
        elif "sslmode=disable" in database_url:
            database_url = database_url.replace("?sslmode=disable", "").replace("&sslmode=disable", "")
        
        self.database_url = database_url
        
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            connect_args=connect_args,
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def init(self) -> None:
        """Initialize database (create tables)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized")
    
    async def close(self) -> None:
        """Close database connection."""
        await self.engine.dispose()
        logger.info("Database connection closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.
        
        Yields:
            AsyncSession for database operations
        """
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def get_session(self) -> AsyncSession:
        """Get a session (for dependency injection)."""
        return self.async_session()
    
    async def execute_raw(self, query: str, params: Optional[dict] = None):
        """
        Execute raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        from sqlalchemy import text
        
        async with self.session() as session:
            result = await session.execute(text(query), params or {})
            return result
    
    async def health_check(self) -> bool:
        """
        Check database connectivity.
        
        Returns:
            True if database is accessible
        """
        try:
            await self.execute_raw("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db


def init_database(database_url: str, **kwargs) -> Database:
    """
    Initialize the global database instance.
    
    Args:
        database_url: PostgreSQL connection URL
        **kwargs: Additional database options
        
    Returns:
        Database instance
    """
    global _db
    _db = Database(database_url, **kwargs)
    return _db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.
    
    Yields:
        AsyncSession
    """
    db = get_database()
    async with db.session() as session:
        yield session
