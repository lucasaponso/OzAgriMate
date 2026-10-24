"""Sample bodies copied from section 5 (REST APIs design) of the report."""

FARM_REQUEST = {"name": "Green Valley", "region": "VIC"}
FARM_UPDATE = {"name": "Green Valley North", "region": "VIC"}
READING_REQUEST = {
    "readingId": "r-17",
    "farmId": "farm-101",
    "deviceId": "dev-8",
    "metric": "soilMoisture",
    "value": 18.5,
    "unit": "percent",
    "timestamp": "2026-10-18T02:00:00Z",
}
COMMAND_REQUEST = {"commandId": "cmd-7", "farmId": "farm-101", "deviceId": "pump-2", "action": "START", "durationSeconds": 120}
