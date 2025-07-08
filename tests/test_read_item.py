import pytest
from fastapi.testclient import TestClient
from server import app

@pytest.fixture(scope="function")
def client():
    # Use context manager so FastAPI startup/shutdown events fire
    with TestClient(app) as c:
        yield c

def test_read_item_success(client):
    # First, create an item to read
    create_payload = {
        "jsonrpc": "2.0",
        "method": "create_item",
        "params": {"name": "Read Test", "description": "For read_item"},
        "id": 10
    }
    create_resp = client.post("/rpc", json=create_payload)
    assert create_resp.status_code == 200
    create_json = create_resp.json()
    created = create_json["result"]
    item_id = created["id"]

    # Now read that same item
    read_payload = {
        "jsonrpc": "2.0",
        "method": "read_item",
        "params": {"id": item_id},
        "id": 11
    }
    read_resp = client.post("/rpc", json=read_payload)
    assert read_resp.status_code == 200

    read_json = read_resp.json()
    assert read_json["jsonrpc"] == "2.0"
    assert read_json["id"] == 11

    result = read_json["result"]
    assert result["id"] == item_id
    assert result["name"] == "Read Test"
    assert result["description"] == "For read_item"

def test_read_item_not_found(client):
    # Attempt to read a non-existent item
    read_payload = {
        "jsonrpc": "2.0",
        "method": "read_item",
        "params": {"id": 999999},
        "id": 12
    }
    read_resp = client.post("/rpc", json=read_payload)
    assert read_resp.status_code == 200

    j = read_resp.json()
    assert j["jsonrpc"] == "2.0"
    assert j["id"] == 12
    # Should be an error response, not a result
    assert "error" in j
    assert "Item with id 999999 not found" in j["error"]["message"]