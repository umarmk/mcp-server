import pytest
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)

def test_ping():
    payload = {
        "jsonrpc": "2.0",
        "method": "mcp_ping",
        "id": 1
    }
    response = client.post("/rpc", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result.get("result") == "pong"