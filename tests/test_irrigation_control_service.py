"""APIs 7-8 (Irrigation). Documented statuses: POST 202/400/409, GET 200/404."""

import pytest
from fastapi.testclient import TestClient

from services.irrigation_control_service.main import create_app
from tests.conftest import COMMAND_REQUEST

POST_URL = "/api/v1/irrigation/commands"


@pytest.fixture
def client():
    return TestClient(create_app())


# API 7 - POST /api/v1/irrigation/commands
def test_submit_command_202_matches_design_sample(client):
    r = client.post(POST_URL, json=COMMAND_REQUEST)
    assert r.status_code == 202
    assert r.json() == {"commandId": "cmd-7", "status": "accepted"}
    state = client.app.state
    assert state.authorization.checks == [("farm-manager", "farm-101", "pump-2")]   # authorised first
    assert state.dispatcher.sent[0].topic == "ozagrimate/farm-101/pump-2/commands"  # then dispatched
    assert state.audit_log.entries[-1].action == "IRRIGATION_COMMAND"


def test_identical_retry_is_idempotent_and_not_redispatched(client):
    client.post(POST_URL, json=COMMAND_REQUEST)
    r = client.post(POST_URL, json=COMMAND_REQUEST)
    assert r.status_code == 202
    assert r.json() == {"commandId": "cmd-7", "status": "accepted"}
    assert r.headers["idempotent-replayed"] == "true"
    assert len(client.app.state.dispatcher.sent) == 1  # pump is not started twice


def test_retry_is_authorised_before_deduplication(client):
    client.post(POST_URL, json=COMMAND_REQUEST)
    client.post(POST_URL, json=COMMAND_REQUEST)
    assert len(client.app.state.authorization.checks) == 2  # runtime diagram B: authorise, then de-duplicate


def test_reused_command_id_with_different_content_409(client):
    client.post(POST_URL, json=COMMAND_REQUEST)
    r = client.post(POST_URL, json={**COMMAND_REQUEST, "durationSeconds": 600})
    assert r.status_code == 409
    assert r.json()["type"].endswith("/command-id-conflict")


@pytest.mark.parametrize(
    "change",
    [
        {"action": "OPEN"},                    # not START/STOP
        {"durationSeconds": 0},                # must be positive
        {"durationSeconds": 99999},            # over 4 h limit
        {"durationSeconds": None},             # START needs a duration
        {"action": "STOP"},                    # STOP must not carry a duration
        {"durationSeconds": "two minutes"},
    ],
)
def test_invalid_command_400(client, change):
    r = client.post(POST_URL, json={**COMMAND_REQUEST, **change})
    assert r.status_code == 400
    assert client.app.state.dispatcher.sent == []


def test_stop_without_duration_202(client):
    body = {k: v for k, v in COMMAND_REQUEST.items() if k != "durationSeconds"}
    r = client.post(POST_URL, json={**body, "commandId": "cmd-8", "action": "STOP"})
    assert r.status_code == 202


@pytest.mark.parametrize("change", [{"deviceId": "pump-99"}, {"farmId": "farm-100"}])
def test_device_not_on_farm_400(client, change):
    r = client.post(POST_URL, json={**COMMAND_REQUEST, **change})
    assert r.status_code == 400 and r.json()["type"].endswith("/unknown-device")


# API 8 - GET /api/v1/irrigation/commands/{commandId}
def test_get_command_200_matches_design_sample(client):
    client.post(POST_URL, json=COMMAND_REQUEST)
    r = client.get(f"{POST_URL}/cmd-7")
    assert r.status_code == 200
    assert r.json() == {"commandId": "cmd-7", "farmId": "farm-101", "status": "accepted"}


def test_get_seeded_executed_command_200(client):
    assert client.get(f"{POST_URL}/cmd-5").json() == {"commandId": "cmd-5", "farmId": "farm-100", "status": "executed"}


def test_get_command_404(client):
    r = client.get(f"{POST_URL}/cmd-404")
    assert r.status_code == 404 and r.json()["type"].endswith("/not-found")
