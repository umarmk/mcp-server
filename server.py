from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from jsonrpcserver import method, async_dispatch, Success, Error
import json
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional
from db.connection import init_db_pool, get_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database pool
    await init_db_pool()
    yield
    # Shutdown: Close the database pool
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

@method
async def mcp_ping():
    """Health check for MCP server"""
    return Success("pong")

@method
async def create_item(name: str, description: Optional[str] = None):
    """
    Insert a new item into the items table.
    Returns the created row as JSON-RPC Success result.
    """
    # Get the shared asyncpg pool
    pool = await get_db_pool()

    # Acquire a connection from the pool
    async with pool.acquire() as conn:
        # Execute INSERT and return id, name, description
        row = await conn.fetchrow(
            """
            INSERT INTO items(name, description)
            VALUES($1, $2)
            RETURNING id, name, description
            """,
            name,
            description,
        )

    # Wrap the row in a Success so jsonrpcserver serializes it correctly
    return Success({
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
    })

@method
async def read_item(id: int):
    """
    Fetch an item by its ID.
    Returns Success(row) if found, otherwise an Error.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, name, description
            FROM items
            WHERE id = $1
            """,
            id
        )

    if not row:
        # Return a JSON-RPC error if the item doesn't exist
        return Error(code=-32602, message=f"Item with id {id} not found")

    # Wrap and return the found row
    return Success({
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
    })

@method
async def update_item(
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Update an existing item's name and/or description.
    At least one of `name` or `description` must be provided.
    Returns the updated row, or an Error if item not found or no fields given.
    """
    # Validate input
    if name is None and description is None:
        return Error(code=-32602, message="At least one of 'name' or 'description' must be provided")

    # Build dynamic SET clause
    set_clauses = []
    values = []
    param_index = 1

    if name is not None:
        set_clauses.append(f"name = ${param_index}")
        values.append(name)
        param_index += 1
    if description is not None:
        set_clauses.append(f"description = ${param_index}")
        values.append(description)
        param_index += 1

    # Add the ID as the last parameter
    values.append(id)
    where_clause = f"WHERE id = ${param_index}"

    # Assemble and execute the UPDATE
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            UPDATE items
            SET {', '.join(set_clauses)}
            {where_clause}
            RETURNING id, name, description
            """,
            *values
        )

    # Handle not-found
    if not row:
        return Error(code=-32602, message=f"Item with id {id} not found")

    # Return success
    return Success({
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
    })

@method
async def delete_item(id: int):
    """
    Delete an item by its ID.
    Returns Success({"id": id}) if deleted, otherwise an Error.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Use DELETE ... RETURNING to know if a row was removed
        row = await conn.fetchrow(
            """
            DELETE FROM items
            WHERE id = $1
            RETURNING id
            """,
            id
        )

    if not row:
        return Error(code=-32602, message=f"Item with id {id} not found")

    return Success({"id": row["id"]})

@method
async def query_items(
    name_filter: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """
    Return a page of items, optionally filtering by name substring.
    - name_filter: case-insensitive substring to match in `name`.
    - limit: max number of items to return.
    - offset: number of items to skip.
    Responds with:
      {
        "items": [ {id, name, description}, ... ],
        "total": <total matching rows>,
        "limit": <limit>,
        "offset": <offset>
      }
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Build WHERE clause if filtering
        where_clause = ""
        values = []
        idx = 1
        if name_filter:
            where_clause = f"WHERE name ILIKE ${idx}"
            values.append(f"%{name_filter}%")
            idx += 1

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM items {where_clause}"
        total = await conn.fetchval(count_sql, *values)

        # Fetch paginated rows
        # Add limit and offset placeholders
        values.extend([limit, offset])
        limit_placeholder = f"${idx}"
        offset_placeholder = f"${idx+1}"
        query_sql = (
            f"SELECT id, name, description FROM items "
            f"{where_clause} "
            f"ORDER BY id "
            f"LIMIT {limit_placeholder} OFFSET {offset_placeholder}"
        )
        rows = await conn.fetch(query_sql, *values)

    # Serialize rows
    items = [
        {"id": r["id"], "name": r["name"], "description": r["description"]}
        for r in rows
    ]
    return Success({
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    })

@app.post("/rpc")
async def rpc_endpoint(request: Request):
    # Read raw bytes from the HTTP request
    raw_body = await request.body()
    # Decode bytes to a UTF-8 string
    body_str = raw_body.decode("utf-8")

    # Dispatch that JSON string to jsonrpcserver
    raw_response = await async_dispatch(body_str)

    # Parse the JSON-RPC response string into a dict
    if isinstance(raw_response, str):
        parsed = json.loads(raw_response)
    else:
        parsed = raw_response

    # Return a proper JSONResponse so response.json() is a dict
    return JSONResponse(content=parsed)

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

