"""PostgreSQL async connection pool management.

Provides AsyncPostgresPool for managing asyncpg connection pools
with proper lifecycle management and query execution methods.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import asyncpg
from asyncpg import Pool, Connection

from supernova.config import get_settings

logger = logging.getLogger(__name__)


class AsyncPostgresPool:
    """Async PostgreSQL connection pool manager.
    
    Manages a connection pool with proper initialization,
    query execution methods, and lifecycle management.
    
    Example:
        >>> pool = AsyncPostgresPool()
        >>> await pool.connect()
        >>> result = await pool.fetch("SELECT * FROM users")
        >>> await pool.disconnect()
    """
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: int = 60,
    ) -> None:
        """Initialize the pool manager.
        
        Args:
            dsn: Database connection string. If None, uses config.
            min_size: Minimum pool size. Default 5.
            max_size: Maximum pool size. Default 20.
            command_timeout: Query timeout in seconds. Default 60.
        """
        self._pool: Optional[Pool] = None
        self._dsn = dsn or get_settings().database_url
        self._min_size = min_size
        self._max_size = max_size
        self._command_timeout = command_timeout
    
    async def connect(self) -> None:
        """Initialize the connection pool.
        
        Creates the pool with configured settings and registers
        the timezone setup callback.
        """
        if self._pool is not None:
            logger.warning("Pool already initialized, skipping connect()")
            return
        
        logger.info(
            f"Creating PostgreSQL pool (min={self._min_size}, max={self._max_size})"
        )
        
        self._pool = await asyncpg.create_pool(
            dsn=self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
            command_timeout=self._command_timeout,
            init=self._init_connection,
        )
        
        logger.info("PostgreSQL pool created successfully")
    
    async def _init_connection(self, conn: Connection) -> None:
        """Initialize a new connection.
        
        Sets timezone to UTC and any other connection-level settings.
        This is called for each new connection in the pool.
        """
        await conn.execute("SET timezone='UTC'")
    
    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool is None:
            logger.warning("Pool not initialized, skipping disconnect()")
            return
        
        logger.info("Closing PostgreSQL pool")
        await self._pool.close()
        self._pool = None
        logger.info("PostgreSQL pool closed")
    
    def get_pool(self) -> Pool:
        """Get the connection pool.
        
        Returns:
            The asyncpg Pool instance.
            
        Raises:
            RuntimeError: If pool is not initialized.
        """
        if self._pool is None:
            raise RuntimeError("Pool not initialized. Call connect() first.")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection, None]:
        """Acquire a connection from the pool.
        
        Usage:
            >>> async with pool.acquire() as conn:
            ...     result = await conn.fetch("SELECT 1")
        """
        pool = self.get_pool()
        async with pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args: Any) -> str:
        """Execute a query.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            Status message from the query.
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(
        self, 
        query: str, 
        *args: Any
    ) -> list[asyncpg.Record]:
        """Fetch multiple rows.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            List of records.
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(
        self, 
        query: str, 
        *args: Any
    ) -> Optional[asyncpg.Record]:
        """Fetch a single row.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            Single record or None if no results.
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(
        self, 
        query: str, 
        *args: Any
    ) -> Any:
        """Fetch a single value.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            Single value or None if no results.
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def executemany(
        self, 
        query: str, 
        args: list[tuple[Any, ...]]
    ) -> None:
        """Execute a query multiple times.
        
        Args:
            query: SQL query string.
            args: List of parameter tuples.
        """
        async with self.acquire() as conn:
            await conn.executemany(query, args)


# Global pool instance
_pool_instance: Optional[AsyncPostgresPool] = None


async def get_postgres_pool() -> AsyncPostgresPool:
    """Get or create the global PostgreSQL pool.
    
    Returns:
        AsyncPostgresPool instance.
    """
    global _pool_instance
    if _pool_instance is None:
        _pool_instance = AsyncPostgresPool()
        await _pool_instance.connect()
    return _pool_instance


async def close_postgres_pool() -> None:
    """Close the global PostgreSQL pool."""
    global _pool_instance
    if _pool_instance is not None:
        await _pool_instance.disconnect()
        _pool_instance = None
