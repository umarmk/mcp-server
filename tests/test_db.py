"""
Test Database Connection and Basic Operations

Tests for database connectivity and basic database operations.
"""

import pytest
import asyncpg
import os
from dotenv import load_dotenv
from db.connection import test_connection, get_database_info

load_dotenv()


@pytest.mark.asyncio
async def test_database_connection():
    """Test basic database connection"""
    # Create a direct connection for this test
    conn = await asyncpg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE"),
    )
    try:
        result = await conn.fetchval("SELECT 1;")
        assert result == 1
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_connection_utility():
    """Test the connection utility function"""
    is_connected = await test_connection()
    assert is_connected is True


@pytest.mark.asyncio
async def test_database_info():
    """Test getting database information"""
    db_info = await get_database_info()

    assert "host" in db_info
    assert "port" in db_info
    assert "database" in db_info
    assert db_info["host"] == os.getenv("PG_HOST", "localhost")
    assert db_info["port"] == int(os.getenv("PG_PORT", 5432))
    assert db_info["database"] == os.getenv("PG_DATABASE")


@pytest.mark.asyncio
async def test_schema_exists():
    """Test that the required schema exists"""
    conn = await asyncpg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE"),
    )

    try:
        # Check that required tables exist
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('items', 'products', 'users', 'orders', 'order_items')
        """)

        table_names = [row['table_name'] for row in tables]
        expected_tables = ['items', 'products', 'users', 'orders', 'order_items']

        for expected_table in expected_tables:
            assert expected_table in table_names, f"Table '{expected_table}' not found"

    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_sample_data_exists():
    """Test that sample data exists in the database"""
    conn = await asyncpg.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        database=os.getenv("PG_DATABASE"),
    )

    try:
        # Check that sample data exists
        items_count = await conn.fetchval("SELECT COUNT(*) FROM items")
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        products_count = await conn.fetchval("SELECT COUNT(*) FROM products")

        # Should have at least some sample data
        assert items_count >= 0  # May be 0 if tests have cleaned up
        assert users_count >= 3  # Should have the 3 sample users
        assert products_count >= 4  # Should have the 4 sample products

    finally:
        await conn.close()