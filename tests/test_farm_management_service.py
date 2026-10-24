"""APIs 1-4 (Farm). Documented statuses: GET 200/404, POST 201/400, PUT 200/400/404, DELETE 204/404."""

import pytest
from fastapi.testclient import TestClient

from services.farm_management_service.main import create_app
from tests.conftest import FARM_REQUEST, FARM_UPDATE

BASE = "/api/v1/farms"


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def farm_id(client):
    return client.post(BASE, json=FARM_REQUEST).json()["id"]


# API 2 - POST /api/v1/farms
def test_register_farm_201_matches_design_sample(client):
    r = client.post(BASE, json=FARM_REQUEST)
    assert r.status_code == 201
    assert r.json() == {"id": "farm-101", "name": "Green Valley", "region": "VIC"}
    assert r.headers["location"] == "/api/v1/farms/farm-101"
    assert client.app.state.event_publisher.published[-1].event_type == "FarmRegistered"


@pytest.mark.parametrize(
    "body",
    [
        {"region": "VIC"},                                   # missing name
        {"name": "   ", "region": "VIC"},                    # blank name
        {"name": "Green Valley", "region": "Victoria"},      # not a state/territory code
        {"name": "Green Valley", "region": "VIC", "x": 1},   # unknown field
    ],
)
def test_register_farm_400_invalid_body(client, body):
    r = client.post(BASE, json=body)
    assert r.status_code == 400
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["errors"]


def test_register_farm_400_malformed_json(client):
    r = client.post(BASE, content=b"{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 400


# API 1 - GET /api/v1/farms/{id}
def test_get_farm_200(client, farm_id):
    r = client.get(f"{BASE}/{farm_id}")
    assert r.status_code == 200
    assert r.json() == {"id": "farm-101", "name": "Green Valley", "region": "VIC"}


def test_get_seeded_farm_200(client):
    assert client.get(f"{BASE}/farm-100").json()["name"] == "Riverina Plains"


def test_get_farm_404(client):
    r = client.get(f"{BASE}/farm-999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Farm 'farm-999' does not exist."


# API 3 - PUT /api/v1/farms/{id}
def test_update_farm_200_matches_design_sample(client, farm_id):
    r = client.put(f"{BASE}/{farm_id}", json=FARM_UPDATE)
    assert r.status_code == 200
    assert r.json() == {"id": "farm-101", "name": "Green Valley North", "region": "VIC"}
    assert client.get(f"{BASE}/{farm_id}").json()["name"] == "Green Valley North"


def test_update_farm_400(client, farm_id):
    assert client.put(f"{BASE}/{farm_id}", json={"name": "Green Valley North"}).status_code == 400


def test_update_farm_404(client):
    assert client.put(f"{BASE}/farm-999", json=FARM_UPDATE).status_code == 404


# API 4 - DELETE /api/v1/farms/{id}
def test_delete_farm_204_then_404(client, farm_id):
    r = client.delete(f"{BASE}/{farm_id}")
    assert r.status_code == 204 and r.content == b""
    assert client.get(f"{BASE}/{farm_id}").status_code == 404
    assert client.delete(f"{BASE}/{farm_id}").status_code == 404
    assert client.app.state.event_publisher.published[-1].event_type == "FarmDeleted"


def test_ids_are_not_reused_after_delete(client, farm_id):
    client.delete(f"{BASE}/{farm_id}")
    assert client.post(BASE, json=FARM_REQUEST).json()["id"] == "farm-102"
