import pytest
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_select_one():
    # Create a direct connection for this test to avoid pool conflicts
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



            