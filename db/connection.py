"""
Database Connection Utilities for PostgreSQL MCP Server

This module provides utilities for managing PostgreSQL connections
and connection pooling for the MCP server.

Note: This module is kept for backward compatibility with existing tests.
The main MCP server uses its own connection management in postgres_mcp_server.py
"""

import os
import logging
from typing import Optional

import asyncpg
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Read connection settings from environment
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")

# Global pool object
_pool: Optional[asyncpg.Pool] = None


async def init_db_pool():
    """
    Initialize the global Postgres connection pool.
    Call this once at application startup.
    """
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(
                host=PG_HOST,
                port=PG_PORT,
                user=PG_USER,
                password=PG_PASSWORD,
                database=PG_DATABASE,
                min_size=1,
                max_size=10,
                command_timeout=60,
            )
            logger.info(f"Database pool initialized: {PG_DATABASE}@{PG_HOST}:{PG_PORT}")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    return _pool


async def get_db_pool() -> asyncpg.Pool:
    """
    Returns the initialized pool, or raises if not yet initialized.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _pool


async def close_db_pool():
    """
    Close the database pool and reset the global variable.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def test_connection() -> bool:
    """
    Test the database connection with current settings.
    Returns True if connection is successful, False otherwise.
    """
    try:
        conn = await asyncpg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def get_database_info() -> dict:
    """
    Get basic information about the database.
    """
    try:
        conn = await asyncpg.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )

        version = await conn.fetchval("SELECT version()")
        db_size = await conn.fetchval(
            "SELECT pg_size_pretty(pg_database_size($1))",
            PG_DATABASE
        )

        await conn.close()

        return {
            "host": PG_HOST,
            "port": PG_PORT,
            "database": PG_DATABASE,
            "version": version,
            "size": db_size
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {}

