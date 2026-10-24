# OzAgriMate Platform: REST API implementation (Assignment 4, Group 42L)

Implements the **8 REST APIs in section 5 (REST APIs design)** of the Software Architecture Document, using
**Python / FastAPI** (the container technology in the C4 diagrams) and dummy in-memory data.
The architecture is event-driven microservices (ADR 01): each API lives in the service that owns its data (ADR 07),
and each service runs as its own process.

## The 8 APIs

| # | Method | Endpoint | Service (container) | Success | Errors |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/farms/{id}` | Farm management service | 200 | 404 |
| 2 | POST | `/api/v1/farms` | Farm management service | 201 | 400 |
| 3 | PUT | `/api/v1/farms/{id}` | Farm management service | 200 | 400, 404 |
| 4 | DELETE | `/api/v1/farms/{id}` | Farm management service | 204 | 404 |
| 5 | POST | `/api/v1/telemetry/readings` | Telemetry service | 201 | 400, 409 |
| 6 | GET | `/api/v1/telemetry/farms/{farmId}/latest` | Telemetry service | 200 | 404 |
| 7 | POST | `/api/v1/irrigation/commands` | Irrigation control service | 202 | 400, 409 |
| 8 | GET | `/api/v1/irrigation/commands/{commandId}` | Irrigation control service | 200 | 404 |

Request and response bodies match the samples in the report field for field. The test suite and the Postman
collection both assert this. Error responses use one structured format (ADR 08), RFC 7807 `application/problem+json`:

```json
{"type": "https://api.ozagrimate.com.au/problems/duplicate-reading", "title": "Conflict", "status": 409,
 "detail": "Reading 'r-17' has already been accepted.", "instance": "/api/v1/telemetry/readings", "readingId": "r-17"}
```

## Run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                                           # platform entry point: starts the 3 services
python -m pytest -q                                     # 56 tests
```

| Service | Port | Swagger UI |
|---|---|---|
| Farm management service | 8001 | http://localhost:8001/docs |
| Telemetry service | 8002 | http://localhost:8002/docs |
| Irrigation control service | 8003 | http://localhost:8003/docs |

One service on its own: `uvicorn services.telemetry_service.main:app --port 8002`

### Postman

Import `postman/OzAgriMate.postman_collection.json`. It has 20 requests: each API's documented success case,
then its documented error cases, in report order. Every success request asserts the body equals the report's
sample. **Restart `main.py` before re-running the whole collection**, because data is in memory and the
POST and DELETE requests change it.

## Repository structure ↔ architecture

Top-level folders follow the deployment view. Inside each implemented service, the layers are its components.

```
ozagrimate-platform/
├── main.py                                     platform entry point: starts every service container
├── services/                                   Kubernetes cluster: application containers
│   ├── farm_management_service/                ✅ APIs 1-4   (owns Farm DB)
│   ├── telemetry_service/                      ✅ APIs 5-6   (owns Telemetry DB)
│   ├── irrigation_control_service/             ✅ APIs 7-8   (owns Command DB)
│   ├── authentication_service/                 ── not implemented (README)
│   ├── ai_decision_service/                    ── not implemented (README)
│   ├── alert_service/                          ── not implemented (README)
│   ├── external_data_integration_service/      ── not implemented (README)
│   └── shared/                                 cross-cutting: error contract, event publisher port, audit log
├── platform_infrastructure/                    API gateway (Nginx), MQTT broker, event broker, databases (not implemented)
├── clients/                                    web browser app, mobile app (not implemented)
├── tests/                                      one test module per implemented service
└── postman/                                    Postman collection and its generator
```

Each implemented service has the same layered structure:

```
<service>/
├── main.py              container entry point: wires components together
├── routes/<route>/      one folder per route (farms, telemetry, irrigation)
│   ├── router.py        Controller component: REST endpoints, request validation
│   ├── service.py       Service component: use cases and business rules
│   └── schemas.py       request/response contracts (the documented API)
├── domain/              entities and enums owned by this service
└── infrastructure/      repositories (database stand-ins), adapters to brokers and other services
```

Services never import each other's code. Their only shared dependency is `services/shared`, so each one can be
built and deployed on its own (ADR 01, ADR 07).

### Components per container (for the component view diagrams)

**Farm management service** (APIs 1-4)

| Component | Responsibility | Module |
|---|---|---|
| Farm Controller | REST endpoints, request validation (400) | `routes/farms/router.py`, `routes/farms/schemas.py` |
| Farm Service | Register, read, update and delete farms; publish farm events | `routes/farms/service.py` |
| Farm Repository | Persist farm records (Farm DB) | `infrastructure/farm_repository.py` |
| Event Publisher | Publish `FarmRegistered/Updated/Deleted` to the event broker | `shared/events.py` |

**Telemetry service** (APIs 5-6, runtime diagram A)

| Component | Responsibility | Module |
|---|---|---|
| Telemetry Controller | REST endpoints, request validation | `routes/telemetry/router.py`, `routes/telemetry/schemas.py` |
| Telemetry Service | Orchestrates validate → de-duplicate → store → publish; latest-reading query | `routes/telemetry/service.py` |
| Reading Validator | Device ownership, metric, unit, range, timestamp checks (400) | `routes/telemetry/reading_validator.py` |
| Reading Repository | Stores readings with unique IDs; rejects duplicates (409) | `infrastructure/reading_repository.py` |
| Device Registry | Devices provisioned per farm | `infrastructure/device_registry.py` |
| MQTT Reading Adapter | Maps MQTT gateway messages to the same use case | `infrastructure/mqtt_reading_adapter.py` |
| Event Publisher | Publishes `ReadingAccepted` (AMQP) | `shared/events.py` |

**Irrigation control service** (APIs 7-8, runtime diagram B)

| Component | Responsibility | Module |
|---|---|---|
| Command Controller | REST endpoints, request validation | `routes/irrigation/router.py`, `routes/irrigation/schemas.py` |
| Command Service | Validate device → authorise → de-duplicate → record → dispatch (runtime diagram B order) | `routes/irrigation/service.py` |
| Authorization Client | Calls the Authorization service to check farm permissions | `infrastructure/authorization_client.py` |
| Command Repository | Stores commands and execution status (Command DB) | `infrastructure/command_repository.py` |
| Device Registry | Irrigation equipment per farm | `infrastructure/device_registry.py` |
| Gateway Command Dispatcher | Publishes the authorised command to the farm gateway over MQTT | `infrastructure/gateway_command_dispatcher.py` |
| Audit Log | Records every irrigation command (ADR 06) | `shared/audit.py` |

## Behaviour behind the documented status codes

- **API 2/3, 400:** missing or blank `name`, `region` not an Australian state/territory code (`VIC`, `NSW`, …), unknown fields, malformed JSON.
- **API 5, 400:** unknown metric, value out of range (e.g. soil moisture > 100 percent), wrong unit, device not registered to the farm, timestamp in the future.
- **API 5, 409:** `readingId` already accepted, or the same device/metric/timestamp sent again under a new ID. Duplicates are not re-published.
- **API 6:** returns the newest reading per device and metric. 404 when the farm has no telemetry.
- **API 7, 202 / 409 (idempotent command):** resending the *same* command with the same `commandId` returns the original 202 with header `Idempotent-Replayed: true`, and the pump is **not** dispatched twice. Reusing a `commandId` for a *different* command returns 409.
- **API 7, 400:** action not `START`/`STOP`, `START` without `durationSeconds` (1–14,400 s), `STOP` with a duration, device not on the farm.
- **API 7/8, status:** `accepted` means authorised, recorded and dispatched. Physical execution is confirmed separately by the gateway (`executed`/`failed`), per ADR 08. Seeded command `cmd-5` shows `executed`.

## Seeded dummy data

| Service | Data |
|---|---|
| Farm management | `farm-100` Riverina Plains (NSW). The next registered farm gets `farm-101`, as in the report samples. |
| Telemetry | Devices `dev-8` (soil moisture, soil temperature) and `dev-9` on farm-101; `dev-3`, `dev-4` on farm-100. Readings `r-10..r-12` exist for farm-100 only. |
| Irrigation control | Equipment `pump-2` and `valve-4` on farm-101, `pump-1` on farm-100. Command `cmd-5` (executed) on farm-100. |

Each service keeps only the farm and device references it needs, rather than reading another service's
database (ADR 07). In production these references are kept current from farm and device events.

## Out of scope (brief, Note 4)

The UI, the API gateway, the event bus, databases and the Authentication service are not implemented. The
Irrigation control service calls authorisation through `AuthorizationClient`, and this prototype uses a stub
that allows every request. Replacing the stub with an HTTP client for the Authentication service needs no
change to the application layer.
