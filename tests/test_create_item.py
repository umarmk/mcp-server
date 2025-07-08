from fastapi.testclient import TestClient
from server import app

def test_create_item_rpc():
    # Use TestClient as context manager to trigger lifespan events
    with TestClient(app) as client:
        # Prepare JSON-RPC payload
        payload = {
            "jsonrpc": "2.0",
            "method": "create_item",
            "params": {
                "name": "Test Item",
                "description": "This is a test"
            },
            "id": 1
        }

        # Send request
        response = client.post("/rpc", json=payload)
        assert response.status_code == 200

        # Parse and verify JSON-RPC response
        resp_json = response.json()
        assert resp_json["jsonrpc"] == "2.0"
        assert resp_json["id"] == 1

        result = resp_json["result"]
        assert result["name"] == "Test Item"
        assert result["description"] == "This is a test"
        assert isinstance(result["id"], int)