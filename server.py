from fastapi import FastAPI, Request
from jsonrpcserver import method, async_dispatch, Success
import json
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

@method
async def mcp_ping():
    """Health check for MCP server"""
    return Success("pong")

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

