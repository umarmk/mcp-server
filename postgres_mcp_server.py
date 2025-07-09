#!/usr/bin/env python3
"""
PostgreSQL MCP Server

A comprehensive Model Context Protocol (MCP) server that provides CRUD operations
and advanced querying capabilities for PostgreSQL databases. This server allows
LLMs to interact with PostgreSQL databases through standardized MCP tools.

Features:
- Complete CRUD operations (Create, Read, Update, Delete)
- Advanced querying with filtering, sorting, and pagination
- Schema introspection and table management
- Connection pooling and error handling
- Proper MCP protocol implementation
- Custom SQL query execution
- Table statistics and analysis

Usage:
    python postgres_mcp_server.py

For Claude Desktop integration:
    mcp install postgres_mcp_server.py --name "PostgreSQL CRUD Server"

Environment Variables Required:
    PG_HOST: PostgreSQL host (default: localhost)
    PG_PORT: PostgreSQL port (default: 5432)
    PG_USER: PostgreSQL username (required)
    PG_PASSWORD: PostgreSQL password (required)
    PG_DATABASE: PostgreSQL database name (required)
"""

import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from datetime import datetime, date

import asyncpg
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DATABASE = os.getenv("PG_DATABASE")


class DatabaseContext:
    """Database context for the MCP server with connection pooling and utilities"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute_single(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query that returns a single row"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def execute_command(self, query: str, *args) -> str:
        """Execute an INSERT/UPDATE/DELETE command and return status"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *args)
            return result
    
    def serialize_value(self, value: Any) -> Any:
        """Serialize database values for JSON compatibility"""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, (list, tuple)):
            return [self.serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        return value


@asynccontextmanager
async def server_lifespan(_: FastMCP) -> AsyncIterator[DatabaseContext]:
    """Manage server startup and shutdown lifecycle with enhanced error handling"""
    logger.info("Starting PostgreSQL MCP Server...")
    
    # Validate required environment variables
    required_vars = ["PG_USER", "PG_PASSWORD", "PG_DATABASE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Initialize database pool on startup
    try:
        pool = await asyncpg.create_pool(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE,
            min_size=2,
            max_size=20,
            command_timeout=60,
        )
        logger.info(f"Connected to PostgreSQL database: {PG_DATABASE}@{PG_HOST}:{PG_PORT}")
        
        # Test the connection
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        yield DatabaseContext(pool=pool)
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    finally:
        # Clean up on shutdown
        if 'pool' in locals():
            await pool.close()
            logger.info("Database connection pool closed")


# Create the MCP server with lifespan management
mcp = FastMCP("PostgreSQL MCP Server", lifespan=server_lifespan)


# =============================================================================
# HEALTH CHECK AND UTILITY TOOLS
# =============================================================================

@mcp.tool()
async def ping() -> str:
    """Health check for the MCP server"""
    return "pong"


@mcp.tool()
async def get_server_info(ctx: Context) -> Dict[str, Any]:
    """Get information about the MCP server and database connection"""
    db_ctx: DatabaseContext = ctx.lifespan_context
    
    try:
        # Get database version and basic info
        version_info = await db_ctx.execute_single("SELECT version() as version")
        db_size = await db_ctx.execute_single(
            "SELECT pg_size_pretty(pg_database_size($1)) as size", 
            PG_DATABASE
        )
        
        return {
            "server_name": "PostgreSQL MCP Server",
            "database": PG_DATABASE,
            "host": PG_HOST,
            "port": PG_PORT,
            "version": version_info["version"] if version_info else "Unknown",
            "database_size": db_size["size"] if db_size else "Unknown",
            "status": "connected"
        }
    except Exception as e:
        return {
            "server_name": "PostgreSQL MCP Server",
            "status": "error",
            "error": str(e)
        }


# =============================================================================
# SCHEMA INTROSPECTION TOOLS
# =============================================================================

@mcp.tool()
async def list_tables(ctx: Context, schema: str = "public") -> List[Dict[str, Any]]:
    """
    List all tables in the specified schema
    
    Args:
        schema: Database schema name (default: 'public')
        
    Returns:
        List of tables with their metadata
    """
    db_ctx: DatabaseContext = ctx.lifespan_context
    
    query = """
        SELECT 
            table_name,
            table_type,
            is_insertable_into,
            is_typed
        FROM information_schema.tables 
        WHERE table_schema = $1
        ORDER BY table_name
    """
    
    tables = await db_ctx.execute_query(query, schema)
    return tables


@mcp.tool()
async def describe_table(ctx: Context, table_name: str, schema: str = "public") -> Dict[str, Any]:
    """
    Get detailed information about a specific table including columns, constraints, and indexes
    
    Args:
        table_name: Name of the table to describe
        schema: Database schema name (default: 'public')
        
    Returns:
        Detailed table information including columns, constraints, and indexes
    """
    db_ctx: DatabaseContext = ctx.lifespan_context
    
    # Get column information
    columns_query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            ordinal_position
        FROM information_schema.columns 
        WHERE table_schema = $1 AND table_name = $2
        ORDER BY ordinal_position
    """
    
    # Get constraints
    constraints_query = """
        SELECT 
            constraint_name,
            constraint_type,
            column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu 
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_schema = $1 AND tc.table_name = $2
    """
    
    # Get indexes
    indexes_query = """
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = $1 AND tablename = $2
    """
    
    columns = await db_ctx.execute_query(columns_query, schema, table_name)
    constraints = await db_ctx.execute_query(constraints_query, schema, table_name)
    indexes = await db_ctx.execute_query(indexes_query, schema, table_name)
    
    if not columns:
        raise ValueError(f"Table '{schema}.{table_name}' not found")
    
    return {
        "table_name": table_name,
        "schema": schema,
        "columns": columns,
        "constraints": constraints,
        "indexes": indexes
    }


# =============================================================================
# CRUD OPERATIONS
# =============================================================================

@mcp.tool()
async def insert_record(
    ctx: Context,
    table_name: str,
    data: Dict[str, Any],
    schema: str = "public",
    return_record: bool = True
) -> Dict[str, Any]:
    """
    Insert a new record into the specified table

    Args:
        table_name: Name of the table to insert into
        data: Dictionary of column names and values to insert
        schema: Database schema name (default: 'public')
        return_record: Whether to return the inserted record (default: True)

    Returns:
        Dictionary containing the inserted record or operation status
    """
    db_ctx: DatabaseContext = ctx.lifespan_context

    if not data:
        raise ValueError("Data dictionary cannot be empty")

    # Build the INSERT query
    columns = list(data.keys())
    placeholders = [f"${i+1}" for i in range(len(columns))]
    values = [data[col] for col in columns]

    base_query = f"""
        INSERT INTO {schema}.{table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
    """

    if return_record:
        query = base_query + " RETURNING *"
        result = await db_ctx.execute_single(query, *values)
        if result:
            return {"success": True, "record": db_ctx.serialize_value(result)}
        else:
            return {"success": False, "error": "Failed to insert record"}
    else:
        result = await db_ctx.execute_command(base_query, *values)
        return {"success": True, "rows_affected": int(result.split()[-1])}


@mcp.tool()
async def select_records(
    ctx: Context,
    table_name: str,
    schema: str = "public",
    columns: Optional[List[str]] = None,
    where_clause: Optional[str] = None,
    where_params: Optional[List[Any]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """
    Select records from the specified table with advanced filtering options

    Args:
        table_name: Name of the table to select from
        schema: Database schema name (default: 'public')
        columns: List of column names to select (default: all columns)
        where_clause: WHERE clause without the 'WHERE' keyword (e.g., 'id = $1 AND name LIKE $2')
        where_params: Parameters for the WHERE clause
        order_by: ORDER BY clause without the 'ORDER BY' keyword (e.g., 'name ASC, id DESC')
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        Dictionary containing the selected records and metadata
    """
    db_ctx: DatabaseContext = ctx.lifespan_context

    # Build the SELECT query
    select_columns = ", ".join(columns) if columns else "*"
    query = f"SELECT {select_columns} FROM {schema}.{table_name}"
    params = []

    if where_clause:
        query += f" WHERE {where_clause}"
        if where_params:
            params.extend(where_params)

    if order_by:
        query += f" ORDER BY {order_by}"

    if limit is not None:
        query += f" LIMIT ${len(params) + 1}"
        params.append(limit)

    if offset is not None:
        query += f" OFFSET ${len(params) + 1}"
        params.append(offset)

    records = await db_ctx.execute_query(query, *params)

    # Get total count for pagination info
    count_query = f"SELECT COUNT(*) as total FROM {schema}.{table_name}"
    if where_clause:
        count_query += f" WHERE {where_clause}"
        count_params = where_params or []
    else:
        count_params = []

    count_result = await db_ctx.execute_single(count_query, *count_params)
    total_count = count_result["total"] if count_result else 0

    return {
        "records": [db_ctx.serialize_value(record) for record in records],
        "total_count": total_count,
        "returned_count": len(records),
        "limit": limit,
        "offset": offset or 0
    }


@mcp.tool()
async def update_records(
    ctx: Context,
    table_name: str,
    data: Dict[str, Any],
    where_clause: str,
    where_params: List[Any],
    schema: str = "public",
    return_records: bool = True
) -> Dict[str, Any]:
    """
    Update records in the specified table

    Args:
        table_name: Name of the table to update
        data: Dictionary of column names and new values
        where_clause: WHERE clause without the 'WHERE' keyword (required for safety)
        where_params: Parameters for the WHERE clause
        schema: Database schema name (default: 'public')
        return_records: Whether to return the updated records (default: True)

    Returns:
        Dictionary containing the updated records or operation status
    """
    db_ctx: DatabaseContext = ctx.lifespan_context

    if not data:
        raise ValueError("Data dictionary cannot be empty")

    if not where_clause:
        raise ValueError("WHERE clause is required for UPDATE operations for safety")

    # Build the UPDATE query
    set_clauses = []
    values = []
    param_index = 1

    for column, value in data.items():
        set_clauses.append(f"{column} = ${param_index}")
        values.append(value)
        param_index += 1

    # Add WHERE parameters
    values.extend(where_params)

    # Adjust WHERE clause parameter indices
    adjusted_where = where_clause
    for i, _ in enumerate(where_params):
        adjusted_where = adjusted_where.replace(f"${i+1}", f"${param_index + i}")

    base_query = f"""
        UPDATE {schema}.{table_name}
        SET {', '.join(set_clauses)}
        WHERE {adjusted_where}
    """

    if return_records:
        query = base_query + " RETURNING *"
        records = await db_ctx.execute_query(query, *values)
        return {
            "success": True,
            "records": [db_ctx.serialize_value(record) for record in records],
            "rows_affected": len(records)
        }
    else:
        result = await db_ctx.execute_command(base_query, *values)
        return {"success": True, "rows_affected": int(result.split()[-1])}


@mcp.tool()
async def delete_records(
    ctx: Context,
    table_name: str,
    where_clause: str,
    where_params: List[Any],
    schema: str = "public",
    return_records: bool = False
) -> Dict[str, Any]:
    """
    Delete records from the specified table

    Args:
        table_name: Name of the table to delete from
        where_clause: WHERE clause without the 'WHERE' keyword (required for safety)
        where_params: Parameters for the WHERE clause
        schema: Database schema name (default: 'public')
        return_records: Whether to return the deleted records (default: False)

    Returns:
        Dictionary containing the deleted records or operation status
    """
    db_ctx: DatabaseContext = ctx.lifespan_context

    if not where_clause:
        raise ValueError("WHERE clause is required for DELETE operations for safety")

    base_query = f"DELETE FROM {schema}.{table_name} WHERE {where_clause}"

    if return_records:
        query = base_query + " RETURNING *"
        records = await db_ctx.execute_query(query, *where_params)
        return {
            "success": True,
            "records": [db_ctx.serialize_value(record) for record in records],
            "rows_affected": len(records)
        }
    else:
        result = await db_ctx.execute_command(base_query, *where_params)
        return {"success": True, "rows_affected": int(result.split()[-1])}


# =============================================================================
# ADVANCED QUERY TOOLS
# =============================================================================

@mcp.tool()
async def execute_custom_query(
    ctx: Context,
    query: str,
    params: Optional[List[Any]] = None,
    query_type: str = "SELECT"
) -> Dict[str, Any]:
    """
    Execute a custom SQL query with parameters

    Args:
        query: SQL query to execute
        params: Optional parameters for the query
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE) for safety

    Returns:
        Query results or execution status

    Note:
        This tool allows advanced users to execute custom SQL queries.
        Use with caution and ensure proper parameterization to prevent SQL injection.
    """
    db_ctx: DatabaseContext = ctx.lifespan_context

    if not query.strip():
        raise ValueError("Query cannot be empty")

    # Basic safety check
    query_upper = query.strip().upper()
    if query_type.upper() == "SELECT":
        if not query_upper.startswith("SELECT"):
            raise ValueError("Query must start with SELECT for query_type='SELECT'")

        results = await db_ctx.execute_query(query, *(params or []))
        return {
            "success": True,
            "records": [db_ctx.serialize_value(record) for record in results],
            "record_count": len(results)
        }
    else:
        # For non-SELECT queries
        result = await db_ctx.execute_command(query, *(params or []))
        return {
            "success": True,
            "result": result,
            "rows_affected": int(result.split()[-1]) if result.split()[-1].isdigit() else 0
        }


@mcp.tool()
async def get_table_statistics(ctx: Context, table_name: str, schema: str = "public") -> Dict[str, Any]:
    """
    Get statistics about a table including row count, size, and column statistics

    Args:
        table_name: Name of the table to analyze
        schema: Database schema name (default: 'public')

    Returns:
        Dictionary containing table statistics
    """
    db_ctx: DatabaseContext = ctx.lifespan_context

    # Get basic table info
    table_info_query = """
        SELECT
            schemaname,
            tablename,
            tableowner,
            hasindexes,
            hasrules,
            hastriggers
        FROM pg_tables
        WHERE schemaname = $1 AND tablename = $2
    """

    # Get row count
    count_query = f"SELECT COUNT(*) as row_count FROM {schema}.{table_name}"

    # Get table size
    size_query = """
        SELECT
            pg_size_pretty(pg_total_relation_size($1)) as total_size,
            pg_size_pretty(pg_relation_size($1)) as table_size,
            pg_size_pretty(pg_total_relation_size($1) - pg_relation_size($1)) as index_size
    """

    table_info = await db_ctx.execute_single(table_info_query, schema, table_name)
    row_count = await db_ctx.execute_single(count_query)
    size_info = await db_ctx.execute_single(size_query, f"{schema}.{table_name}")

    if not table_info:
        raise ValueError(f"Table '{schema}.{table_name}' not found")

    return {
        "table_info": table_info,
        "row_count": row_count["row_count"] if row_count else 0,
        "size_info": size_info or {}
    }


def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting PostgreSQL MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
