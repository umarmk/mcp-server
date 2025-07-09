"""
Test MCP Server Basic Functionality

Tests for the PostgreSQL MCP server using the official MCP client.
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
async def test_ping(mcp_session):
    """Test the ping health check tool"""
    result = await mcp_session.call_tool("ping", {})
    assert result.content[0].text == "pong"


@pytest.mark.asyncio
async def test_get_server_info(mcp_session):
    """Test getting server information"""
    result = await mcp_session.call_tool("get_server_info", {})
    server_info = json.loads(result.content[0].text)

    assert "server_name" in server_info
    assert "status" in server_info
    assert server_info["server_name"] == "PostgreSQL CRUD MCP Server"


@pytest.mark.asyncio
async def test_list_tools(mcp_session):
    """Test that all expected tools are available"""
    tools = await mcp_session.list_tools()
    tool_names = [tool.name for tool in tools.tools]

    expected_tools = [
        "ping",
        "get_server_info",
        "list_tables",
        "describe_table",
        "insert_record",
        "select_records",
        "update_records",
        "delete_records",
        "execute_custom_query",
        "get_table_statistics"
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Tool '{expected_tool}' not found"