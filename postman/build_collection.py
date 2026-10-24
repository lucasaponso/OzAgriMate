"""Generates OzAgriMate.postman_collection.json (run: python postman/build_collection.py).

Requests follow the order of the API design (section 5 of the report). Each API has its
documented success case first, then its documented error cases.
"""

import json
from pathlib import Path

OUT = Path(__file__).with_name("OzAgriMate.postman_collection.json")


def req(name, method, base, path, body=None, expect=200, expect_body=None, extra_tests=()):
    tests = [f"pm.test('Status is {expect}', () => pm.response.to.have.status({expect}));"]
    if expect_body is not None:
        tests.append(
            f"pm.test('Body matches API design sample', () => pm.expect(pm.response.json()).to.eql({json.dumps(expect_body)}));"
        )
    tests += list(extra_tests)
    item = {
        "name": name,
        "request": {
            "method": method,
            "header": [{"key": "Content-Type", "value": "application/json"}] if body is not None else [],
            "url": {
                "raw": "{{" + base + "}}" + path,
                "host": ["{{" + base + "}}"],
                "path": [p for p in path.split("/") if p],
            },
        },
        "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": tests}}],
    }
    if body is not None:
        raw = body if isinstance(body, str) else json.dumps(body, indent=2)
        item["request"]["body"] = {"mode": "raw", "raw": raw, "options": {"raw": {"language": "json"}}}
    return item


F, T, I = "farmUrl", "telemetryUrl", "irrigationUrl"
farm = {"name": "Green Valley", "region": "VIC"}
farm_v2 = {"name": "Green Valley North", "region": "VIC"}
reading = {"readingId": "r-17", "farmId": "farm-101", "deviceId": "dev-8", "metric": "soilMoisture",
           "value": 18.5, "unit": "percent", "timestamp": "2026-10-18T02:00:00Z"}
command = {"commandId": "cmd-7", "farmId": "farm-101", "deviceId": "pump-2", "action": "START", "durationSeconds": 120}

folders = [
    ("Farm service (port 8001)", [
        req("API 2 - POST /farms - 201 Created", "POST", F, "/api/v1/farms", farm, 201,
            {"id": "farm-101", "name": "Green Valley", "region": "VIC"}),
        req("API 2 - POST /farms - 400 invalid region", "POST", F, "/api/v1/farms", {"name": "Green Valley", "region": "Victoria"}, 400),
        req("API 1 - GET /farms/{id} - 200 OK", "GET", F, "/api/v1/farms/farm-101", None, 200,
            {"id": "farm-101", "name": "Green Valley", "region": "VIC"}),
        req("API 1 - GET /farms/{id} - 404 Not Found", "GET", F, "/api/v1/farms/farm-999", None, 404),
        req("API 3 - PUT /farms/{id} - 200 OK", "PUT", F, "/api/v1/farms/farm-101", farm_v2, 200,
            {"id": "farm-101", "name": "Green Valley North", "region": "VIC"}),
        req("API 3 - PUT /farms/{id} - 400 missing region", "PUT", F, "/api/v1/farms/farm-101", {"name": "Green Valley North"}, 400),
        req("API 3 - PUT /farms/{id} - 404 Not Found", "PUT", F, "/api/v1/farms/farm-999", farm_v2, 404),
        req("API 4 - DELETE /farms/{id} - 204 No Content", "DELETE", F, "/api/v1/farms/farm-101", None, 204),
        req("API 4 - DELETE /farms/{id} - 404 Not Found", "DELETE", F, "/api/v1/farms/farm-101", None, 404),
    ]),
    ("Telemetry service (port 8002)", [
        req("API 6 - GET latest - 404 before any readings", "GET", T, "/api/v1/telemetry/farms/farm-101/latest", None, 404),
        req("API 5 - POST /telemetry/readings - 201 Created", "POST", T, "/api/v1/telemetry/readings", reading, 201,
            {"readingId": "r-17", "status": "accepted"}),
        req("API 5 - POST /telemetry/readings - 409 duplicate readingId", "POST", T, "/api/v1/telemetry/readings", reading, 409),
        req("API 5 - POST /telemetry/readings - 400 value out of range", "POST", T, "/api/v1/telemetry/readings",
            {**reading, "readingId": "r-19", "value": 140}, 400),
        req("API 6 - GET latest - 200 OK", "GET", T, "/api/v1/telemetry/farms/farm-101/latest", None, 200,
            {"farmId": "farm-101", "readings": [{"readingId": "r-17", "metric": "soilMoisture", "value": 18.5, "unit": "percent"}]}),
    ]),
    ("Irrigation service (port 8003)", [
        req("API 7 - POST /irrigation/commands - 202 Accepted", "POST", I, "/api/v1/irrigation/commands", command, 202,
            {"commandId": "cmd-7", "status": "accepted"}),
        req("API 7 - POST /irrigation/commands - 202 idempotent retry (same command)", "POST", I, "/api/v1/irrigation/commands", command, 202,
            {"commandId": "cmd-7", "status": "accepted"},
            ["pm.test('Marked as replay', () => pm.expect(pm.response.headers.get('Idempotent-Replayed')).to.eql('true'));"]),
        req("API 7 - POST /irrigation/commands - 409 commandId reused", "POST", I, "/api/v1/irrigation/commands",
            {**command, "durationSeconds": 600}, 409),
        req("API 7 - POST /irrigation/commands - 400 invalid action", "POST", I, "/api/v1/irrigation/commands",
            {**command, "commandId": "cmd-9", "action": "OPEN"}, 400),
        req("API 8 - GET /irrigation/commands/{commandId} - 200 OK", "GET", I, "/api/v1/irrigation/commands/cmd-7", None, 200,
            {"commandId": "cmd-7", "farmId": "farm-101", "status": "accepted"}),
        req("API 8 - GET /irrigation/commands/{commandId} - 404 Not Found", "GET", I, "/api/v1/irrigation/commands/cmd-404", None, 404),
    ]),
]

collection = {
    "info": {
        "name": "OzAgriMate Platform - 8 REST APIs",
        "description": "Run in order against freshly started services (python main.py). Data is in memory, "
                       "so restart the services before re-running the whole collection.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": [{"name": n, "item": items} for n, items in folders],
    "variable": [
        {"key": F, "value": "http://localhost:8001"},
        {"key": T, "value": "http://localhost:8002"},
        {"key": I, "value": "http://localhost:8003"},
    ],
}

OUT.write_text(json.dumps(collection, indent=2))
print(f"wrote {OUT} ({sum(len(i) for _, i in folders)} requests)")
