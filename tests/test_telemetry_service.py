"""APIs 5-6 (Telemetry). Documented statuses: POST 201/400/409, GET 200/404."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from services.telemetry_service.infrastructure.mqtt_reading_adapter import MqttReadingAdapter
from services.telemetry_service.main import create_app
from tests.conftest import READING_REQUEST

POST_URL = "/api/v1/telemetry/readings"


def latest_url(farm_id):
    return f"/api/v1/telemetry/farms/{farm_id}/latest"


@pytest.fixture
def client():
    return TestClient(create_app())


# API 5 - POST /api/v1/telemetry/readings
def test_submit_reading_201_matches_design_sample(client):
    r = client.post(POST_URL, json=READING_REQUEST)
    assert r.status_code == 201
    assert r.json() == {"readingId": "r-17", "status": "accepted"}
    event = client.app.state.event_publisher.published[-1]
    assert event.event_type == "ReadingAccepted" and event.payload["readingId"] == "r-17"


def test_resubmitted_reading_id_409(client):
    client.post(POST_URL, json=READING_REQUEST)
    r = client.post(POST_URL, json=READING_REQUEST)
    assert r.status_code == 409
    assert r.json()["type"].endswith("/duplicate-reading")
    assert len(client.app.state.event_publisher.published) == 1  # duplicate not re-published


def test_same_measurement_under_new_id_409(client):
    client.post(POST_URL, json=READING_REQUEST)
    r = client.post(POST_URL, json={**READING_REQUEST, "readingId": "r-18"})
    assert r.status_code == 409 and r.json()["readingId"] == "r-17"


@pytest.mark.parametrize(
    "change, problem",
    [
        ({"metric": "humidity"}, "unsupported-metric"),
        ({"metric": "rainfall"}, "unsupported-metric"),          # dev-8 has no rain gauge
        ({"value": 140}, "value-out-of-range"),
        ({"unit": "fraction"}, "unit-mismatch"),
        ({"deviceId": "dev-404"}, "unknown-device"),
        ({"farmId": "farm-100"}, "unknown-device"),              # dev-8 is not on farm-100
    ],
)
def test_invalid_reading_400(client, change, problem):
    r = client.post(POST_URL, json={**READING_REQUEST, **change})
    assert r.status_code == 400
    assert r.json()["type"].endswith(problem)


def test_future_timestamp_400(client):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    assert client.post(POST_URL, json={**READING_REQUEST, "timestamp": future}).status_code == 400


@pytest.mark.parametrize("missing", ["readingId", "farmId", "deviceId", "metric", "value", "unit", "timestamp"])
def test_missing_field_400(client, missing):
    body = {k: v for k, v in READING_REQUEST.items() if k != missing}
    r = client.post(POST_URL, json=body)
    assert r.status_code == 400 and r.json()["errors"][0]["field"] == missing


def test_timestamp_without_timezone_400(client):
    assert client.post(POST_URL, json={**READING_REQUEST, "timestamp": "2026-10-18T02:00:00"}).status_code == 400


# API 6 - GET /api/v1/telemetry/farms/{farmId}/latest
def test_latest_200_matches_design_sample(client):
    client.post(POST_URL, json=READING_REQUEST)
    r = client.get(latest_url("farm-101"))
    assert r.status_code == 200
    assert r.json() == {
        "farmId": "farm-101",
        "readings": [{"readingId": "r-17", "metric": "soilMoisture", "value": 18.5, "unit": "percent"}],
    }


def test_latest_returns_newest_per_device_and_metric(client):
    client.post(POST_URL, json=READING_REQUEST)
    client.post(POST_URL, json={**READING_REQUEST, "readingId": "r-18", "value": 17.9, "timestamp": "2026-10-18T02:15:00Z"})
    client.post(POST_URL, json={**READING_REQUEST, "readingId": "r-16", "value": 19.4, "timestamp": "2026-10-18T01:45:00Z"})
    readings = client.get(latest_url("farm-101")).json()["readings"]
    assert [(x["readingId"], x["value"]) for x in readings] == [("r-18", 17.9)]


def test_latest_seeded_farm_200(client):
    readings = client.get(latest_url("farm-100")).json()["readings"]
    assert {x["readingId"] for x in readings} == {"r-11", "r-12"}


def test_latest_404_when_no_readings(client):
    r = client.get(latest_url("farm-101"))
    assert r.status_code == 404
    assert r.json()["type"].endswith("/not-found")


def test_mqtt_adapter_feeds_same_use_case(client):
    cmd = MqttReadingAdapter().to_command(
        "ozagrimate/farm-101/dev-8/readings",
        b'{"id":"r-30","m":"soilMoisture","v":21.0,"u":"percent","ts":"2026-10-18T03:00:00Z"}',
    )
    reading = client.app.state.telemetry_service.submit_reading(cmd)
    assert reading.reading_id == "r-30"
    assert client.get(latest_url("farm-101")).json()["readings"][0]["readingId"] == "r-30"
