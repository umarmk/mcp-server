"""
Test CRUD Operations for PostgreSQL MCP Server

Tests for create, read, update, and delete operations using the MCP client.
"""

import pytest
import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.fixture
async def mcp_session():
    """Create an MCP client session for testing"""
    server_params = StdioServerParameters(
        command="python",
        args=["postgres_mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.mark.asyncio
async def test_insert_record(mcp_session):
    """Test inserting a new record"""
    insert_data = {
        "name": "Test Item",
        "description": "This is a test item"
    }

    result = await mcp_session.call_tool("insert_record", {
        "table_name": "items",
        "data": insert_data
    })

    response = json.loads(result.content[0].text)
    assert response["success"] is True
    assert "record" in response
    assert response["record"]["name"] == "Test Item"
    assert response["record"]["description"] == "This is a test item"
    assert isinstance(response["record"]["id"], int)


@pytest.mark.asyncio
async def test_select_records(mcp_session):
    """Test selecting records with filtering"""
    # First insert a test record
    insert_data = {"name": "Select Test Item", "description": "For select testing"}

    insert_result = await mcp_session.call_tool("insert_record", {
        "table_name": "items",
        "data": insert_data
    })

    insert_response = json.loads(insert_result.content[0].text)
    record_id = insert_response["record"]["id"]

    # Now select the record
    select_result = await mcp_session.call_tool("select_records", {
        "table_name": "items",
        "where_clause": "id = $1",
        "where_params": [record_id]
    })

    select_response = json.loads(select_result.content[0].text)
    assert select_response["returned_count"] == 1
    assert len(select_response["records"]) == 1
    assert select_response["records"][0]["name"] == "Select Test Item"


@pytest.mark.asyncio
async def test_update_records(mcp_session):
    """Test updating records"""
    # First insert a test record
    insert_data = {"name": "Update Test Item", "description": "Original description"}

    insert_result = await mcp_session.call_tool("insert_record", {
        "table_name": "items",
        "data": insert_data
    })

    insert_response = json.loads(insert_result.content[0].text)
    record_id = insert_response["record"]["id"]

    # Update the record
    update_data = {"description": "Updated description"}

    update_result = await mcp_session.call_tool("update_records", {
        "table_name": "items",
        "data": update_data,
        "where_clause": "id = $1",
        "where_params": [record_id]
    })

    update_response = json.loads(update_result.content[0].text)
    assert update_response["success"] is True
    assert update_response["rows_affected"] == 1
    assert update_response["records"][0]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_records(mcp_session):
    """Test deleting records"""
    # First insert a test record
    insert_data = {"name": "Delete Test Item", "description": "To be deleted"}

    insert_result = await mcp_session.call_tool("insert_record", {
        "table_name": "items",
        "data": insert_data
    })

    insert_response = json.loads(insert_result.content[0].text)
    record_id = insert_response["record"]["id"]

    # Delete the record
    delete_result = await mcp_session.call_tool("delete_records", {
        "table_name": "items",
        "where_clause": "id = $1",
        "where_params": [record_id]
    })

    delete_response = json.loads(delete_result.content[0].text)
    assert delete_response["success"] is True
    assert delete_response["rows_affected"] == 1

    # Verify the record is deleted
    select_result = await mcp_session.call_tool("select_records", {
        "table_name": "items",
        "where_clause": "id = $1",
        "where_params": [record_id]
    })

    select_response = json.loads(select_result.content[0].text)
    assert select_response["returned_count"] == 0