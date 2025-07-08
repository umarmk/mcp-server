import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Read connection settings from environment
PG_HOST     = os.getenv("PG_HOST", "localhost")
PG_PORT     = int(os.getenv("PG_PORT", 5432))
PG_USER     = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")

# Global pool object
_pool: asyncpg.Pool | None = None

async def init_db_pool():
    """
    Initialize the global Postgres connection pool.
    Call this once at application startup.
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE,
            min_size=1,
            max_size=10,
        )
    return _pool

async def get_db_pool() -> asyncpg.Pool:
    """
    Returns the initialized pool, or raises if not yet initialized.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _pool

