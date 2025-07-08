import pytest
from fastapi.testclient import TestClient
from server import app

@pytest.fixture(scope="function")
def client():
    # Each test spins up FastAPI (with DB pool) and tears it down afterward
    with TestClient(app) as c:
        yield c

def create_query_test_items(client):
    """
    Helper: create 3 items whose names share a unique prefix for predictable filtering.
    Returns the list of created IDs in insertion order.
    """
    prefix = "QueryTest_"
    ids = []
    for idx, suffix in enumerate(["A", "B", "C"], start=1):
        payload = {
            "jsonrpc": "2.0",
            "method": "create_item",
            "params": {
                "name": f"{prefix}{suffix}",
                "description": f"desc{suffix}"
            },
            "id": 100 + idx
        }
        resp = client.post("/rpc", json=payload)
        data = resp.json()
        ids.append(data["result"]["id"])
    return prefix, ids

def test_query_items_basic_structure(client):
    # Call with no params to inspect the shape of the response
    payload = {
        "jsonrpc": "2.0",
        "method": "query_items",
        "params": {},
        "id": 200
    }
    resp = client.post("/rpc", json=payload)
    assert resp.status_code == 200
    j = resp.json()
    r = j["result"]
    # Must include these keys
    assert set(r.keys()) == {"items", "total", "limit", "offset"}
    # Defaults
    assert r["limit"] == 10
    assert r["offset"] == 0
    assert isinstance(r["items"], list)
    assert isinstance(r["total"], int)

def test_query_items_filter_and_pagination(client):
    prefix, ids = create_query_test_items(client)

    # Page 1: limit=2, offset=0
    payload1 = {
        "jsonrpc": "2.0",
        "method": "query_items",
        "params": {
            "name_filter": prefix,
            "limit": 2,
            "offset": 0
        },
        "id": 201
    }
    resp1 = client.post("/rpc", json=payload1)
    assert resp1.status_code == 200
    r1 = resp1.json()["result"]

    # Check metadata
    assert r1["limit"] == 2
    assert r1["offset"] == 0
    assert r1["total"] >= 3  # At least our 3 items

    # Exactly 2 items on the first page
    items1 = r1["items"]
    assert len(items1) == 2
    # They must match our prefix and be in ascending ID order
    assert all(item["name"].startswith(prefix) for item in items1)
    page1_ids = [item["id"] for item in items1]

    # Page 2: offset=2
    payload2 = {
        "jsonrpc": "2.0",
        "method": "query_items",
        "params": {
            "name_filter": prefix,
            "limit": 2,
            "offset": 2
        },
        "id": 202
    }
    resp2 = client.post("/rpc", json=payload2)
    assert resp2.status_code == 200
    r2 = resp2.json()["result"]

    assert r2["limit"] == 2
    assert r2["offset"] == 2
    items2 = r2["items"]
    # There should be at least one item (the 3rd)
    assert len(items2) >= 1
    # And none of the IDs should overlap the first page
    assert not any(item["id"] in page1_ids for item in items2)

