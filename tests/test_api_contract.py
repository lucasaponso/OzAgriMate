"""Cross-service checks against the brief: exactly the 8 documented endpoints, and only documented status codes."""

from services.farm_management_service.main import create_app as farm_app
from services.irrigation_control_service.main import create_app as irrigation_app
from services.telemetry_service.main import create_app as telemetry_app

# Section 5 of the report: method, path -> documented HTTP statuses
DOCUMENTED = {
    ("GET", "/api/v1/farms/{id}"): {"200", "404"},
    ("POST", "/api/v1/farms"): {"201", "400"},
    ("PUT", "/api/v1/farms/{id}"): {"200", "400", "404"},
    ("DELETE", "/api/v1/farms/{id}"): {"204", "404"},
    ("POST", "/api/v1/telemetry/readings"): {"201", "400", "409"},
    ("GET", "/api/v1/telemetry/farms/{farmId}/latest"): {"200", "404"},
    ("POST", "/api/v1/irrigation/commands"): {"202", "400", "409"},
    ("GET", "/api/v1/irrigation/commands/{commandId}"): {"200", "404"},
}


def _implemented():
    found = {}
    for make in (farm_app, telemetry_app, irrigation_app):
        for path, ops in make().openapi()["paths"].items():
            for method, op in ops.items():
                found[(method.upper(), path)] = set(op["responses"])
    return found


def test_exactly_the_eight_documented_endpoints():
    assert set(_implemented()) == set(DOCUMENTED)


def test_all_four_http_methods_used():
    assert {m for m, _ in DOCUMENTED} == {"GET", "POST", "PUT", "DELETE"}


def test_openapi_advertises_only_documented_status_codes():
    for endpoint, codes in _implemented().items():
        assert codes == DOCUMENTED[endpoint], endpoint
