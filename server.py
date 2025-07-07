from fastapi import FastAPI, Request
from jsonrpcserver import method, async_dispatch
import uvicorn

app = FastAPI()

@method
async def mcp_ping() -> str:
    """Health check for MCP server"""
    return "pong"

@app.post("/rpc")
async def rpc_endpoint(request: Request):
    request_json = await request.json()
    response = await async_dispatch(request_json)
    return response

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

