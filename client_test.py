#!/usr/bin/env python3
"""
Comprehensive Test Client for PostgreSQL MCP Server

This client demonstrates all the functionality of the PostgreSQL CRUD MCP server
including schema introspection, CRUD operations, and advanced querying.
"""

import asyncio
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def test_health_and_info(session: ClientSession):
    """Test health check and server info tools"""
    print(" Testing health check...")
    result = await session.call_tool("ping", {})
    print(f"  Ping result: {result.content[0].text}")

    print("\n Getting server info...")
    result = await session.call_tool("get_server_info", {})
    server_info = json.loads(result.content[0].text)
    print(f"  Server: {server_info.get('server_name')}")
    print(f"  Database: {server_info.get('database')} @ {server_info.get('host')}:{server_info.get('port')}")
    print(f"  Status: {server_info.get('status')}")


async def test_schema_introspection(session: ClientSession):
    """Test schema introspection tools"""
    print("\n Listing tables...")
    result = await session.call_tool("list_tables", {})
    tables = json.loads(result.content[0].text)
    print(f"  Found {len(tables)} tables:")
    for table in tables[:5]:  # Show first 5 tables
        print(f"    - {table['table_name']} ({table['table_type']})")

    if tables:
        table_name = tables[0]['table_name']
        print(f"\n Describing table '{table_name}'...")
        result = await session.call_tool("describe_table", {"table_name": table_name})
        table_info = json.loads(result.content[0].text)
        print(f"  Columns: {len(table_info['columns'])}")
        print(f"  Constraints: {len(table_info['constraints'])}")
        print(f"  Indexes: {len(table_info['indexes'])}")


async def test_crud_operations(session: ClientSession):
    """Test CRUD operations"""
    print("\n Testing INSERT operation...")
    insert_data = {
        "name": "MCP Test Item",
        "description": "Created via MCP client test"
    }
    result = await session.call_tool("insert_record", {
        "table_name": "items",
        "data": insert_data
    })
    insert_result = json.loads(result.content[0].text)
    print(f"  Insert success: {insert_result['success']}")

    if insert_result['success']:
        record_id = insert_result['record']['id']
        print(f"  Created record ID: {record_id}")

        print("\n Testing SELECT operation...")
        result = await session.call_tool("select_records", {
            "table_name": "items",
            "where_clause": "id = $1",
            "where_params": [record_id],
            "limit": 1
        })
        select_result = json.loads(result.content[0].text)
        print(f"  Found {select_result['returned_count']} record(s)")

        print("\n Testing UPDATE operation...")
        update_data = {"description": "Updated via MCP client test"}
        result = await session.call_tool("update_records", {
            "table_name": "items",
            "data": update_data,
            "where_clause": "id = $1",
            "where_params": [record_id]
        })
        update_result = json.loads(result.content[0].text)
        print(f"  Update success: {update_result['success']}")
        print(f"  Rows affected: {update_result['rows_affected']}")

        print("\n Testing DELETE operation...")
        result = await session.call_tool("delete_records", {
            "table_name": "items",
            "where_clause": "id = $1",
            "where_params": [record_id]
        })
        delete_result = json.loads(result.content[0].text)
        print(f"  Delete success: {delete_result['success']}")
        print(f"  Rows affected: {delete_result['rows_affected']}")


async def test_advanced_queries(session: ClientSession):
    """Test advanced querying capabilities"""
    print("\n Testing advanced SELECT with pagination...")
    result = await session.call_tool("select_records", {
        "table_name": "items",
        "order_by": "created_at DESC",
        "limit": 3,
        "offset": 0
    })
    select_result = json.loads(result.content[0].text)
    print(f"  Total records: {select_result['total_count']}")
    print(f"  Returned: {select_result['returned_count']}")

    print("\n Testing table statistics...")
    result = await session.call_tool("get_table_statistics", {
        "table_name": "items"
    })
    stats = json.loads(result.content[0].text)
    print(f"  Row count: {stats['row_count']}")
    if 'size_info' in stats and stats['size_info']:
        print(f"  Table size: {stats['size_info'].get('table_size', 'Unknown')}")


async def test_custom_query(session: ClientSession):
    """Test custom SQL query execution"""
    print("\n Testing custom query...")
    custom_query = "SELECT COUNT(*) as total_items FROM items"
    result = await session.call_tool("execute_custom_query", {
        "query": custom_query,
        "query_type": "SELECT"
    })
    query_result = json.loads(result.content[0].text)
    print(f"  Query success: {query_result['success']}")
    if query_result['success'] and query_result['records']:
        print(f"  Total items: {query_result['records'][0]['total_items']}")


async def main():
    """Main test function"""
    print("Starting PostgreSQL MCP Server Tests...")

    # Connect to the MCP server using stdio transport
    server_params = StdioServerParameters(
        command="python",
        args=["postgres_mcp_server.py"]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print(" Connected to PostgreSQL MCP server")

                # List available tools
                tools = await session.list_tools()
                print(f"\n Available tools ({len(tools.tools)}):")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")

                # Run all tests
                await test_health_and_info(session)
                await test_schema_introspection(session)
                await test_crud_operations(session)
                await test_advanced_queries(session)
                await test_custom_query(session)

                print("\n All tests completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
