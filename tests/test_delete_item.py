import pytest
from fastapi.testclient import TestClient
from server import app

# Fixture to create a test client for each test
@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c

# Test deleting an item
def test_delete_item_success(client):
    # Create an item
    create_payload = {
        "jsonrpc": "2.0",
        "method": "create_item",
        "params": {"name": "ToDelete", "description": "Will be gone"},
        "id": 30
    }
    cr = client.post("/rpc", json=create_payload).json()
    item_id = cr["result"]["id"]

    # Delete that item
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "delete_item",
        "params": {"id": item_id},
        "id": 31
    }
    resp = client.post("/rpc", json=delete_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 31
    assert data["result"]["id"] == item_id

    # Confirm it’s really gone via read_item
    read_payload = {
        "jsonrpc": "2.0",
        "method": "read_item",
        "params": {"id": item_id},
        "id": 32
    }
    read_resp = client.post("/rpc", json=read_payload).json()
    assert "error" in read_resp
    assert "not found" in read_resp["error"]["message"]

# Test deleting a non-existent item
def test_delete_item_not_found(client):
    # Attempt to delete a non-existent ID
    delete_payload = {
        "jsonrpc": "2.0",
        "method": "delete_item",
        "params": {"id": 999999},
        "id": 33
    }
    resp = client.post("/rpc", json=delete_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == -32602
    assert "not found" in data["error"]["message"]