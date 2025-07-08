import pytest
from fastapi.testclient import TestClient
from server import app

@pytest.fixture(scope="function")
def client():
    # Each test gets its own startup/shutdown and DB pool
    with TestClient(app) as c:
        yield c

def test_update_item_success_name_only(client):
    # Create an item
    create_payload = {
        "jsonrpc": "2.0",
        "method": "create_item",
        "params": {"name": "Original", "description": "Desc"},
        "id": 20
    }
    cr = client.post("/rpc", json=create_payload).json()
    item_id = cr["result"]["id"]

    # Update only the name
    update_payload = {
        "jsonrpc": "2.0",
        "method": "update_item",
        "params": {"id": item_id, "name": "NewName"},
        "id": 21
    }
    resp = client.post("/rpc", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 21
    result = data["result"]
    assert result["id"] == item_id
    assert result["name"] == "NewName"
    assert result["description"] == "Desc"

def test_update_item_success_description_only(client):
    # Create another item
    create_payload = {
        "jsonrpc": "2.0",
        "method": "create_item",
        "params": {"name": "Foo", "description": "Bar"},
        "id": 22
    }
    cr = client.post("/rpc", json=create_payload).json()
    item_id = cr["result"]["id"]

    # Update only the description
    update_payload = {
        "jsonrpc": "2.0",
        "method": "update_item",
        "params": {"id": item_id, "description": "NewDesc"},
        "id": 23
    }
    resp = client.post("/rpc", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    result = data["result"]
    assert result["name"] == "Foo"
    assert result["description"] == "NewDesc"

def test_update_item_not_found(client):
    # Try to update an ID that doesn't exist
    update_payload = {
        "jsonrpc": "2.0",
        "method": "update_item",
        "params": {"id": 999999, "name": "X"},
        "id": 24
    }
    resp = client.post("/rpc", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "not found" in data["error"]["message"]

def test_update_item_no_fields(client):
    # Create one more item
    create_payload = {
        "jsonrpc": "2.0",
        "method": "create_item",
        "params": {"name": "TestNoField", "description": "D"},
        "id": 25
    }
    cr = client.post("/rpc", json=create_payload).json()
    item_id = cr["result"]["id"]

    # Call update_item with no name or description
    update_payload = {
        "jsonrpc": "2.0",
        "method": "update_item",
        "params": {"id": item_id},
        "id": 26
    }
    resp = client.post("/rpc", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "must be provided" in data["error"]["message"]

