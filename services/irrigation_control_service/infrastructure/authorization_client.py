"""Client for the Authorization service ("check user permissions for the farm", runtime diagram B).

In production this calls the Authentication service over HTTP/REST with the caller's
identity, which the API gateway forwards. Neither the gateway nor the Authentication
service is implemented in this prototype (brief, Note 4), so the stub below permits
every request. The port stays in place so the real client can replace it without
changing the application layer.
"""

from __future__ import annotations

from typing import Protocol


class AuthorizationClient(Protocol):
    def can_operate(self, actor: str, farm_id: str, device_id: str) -> bool: ...


class StubAuthorizationClient:
    def __init__(self) -> None:
        self.checks: list[tuple[str, str, str]] = []

    def can_operate(self, actor: str, farm_id: str, device_id: str) -> bool:
        self.checks.append((actor, farm_id, device_id))
        return True
