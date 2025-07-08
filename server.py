from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from jsonrpcserver import method, async_dispatch, Success
import json
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional
from db.connection import init_db_pool, get_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database pool
    await init_db_pool()
    yield
    # Shutdown: Close the database pool
    pool = await get_db_pool()
    await pool.close()

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

