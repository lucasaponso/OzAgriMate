"""In-memory farm store. Stands in for the Farm DB (PostgreSQL) in the deployment view."""

from __future__ import annotations

import threading

from services.farm_management_service.domain.models import Farm, Region


class InMemoryFarmRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # Dummy data. The next generated id is farm-101, as in the API design samples.
        self._farms: dict[str, Farm] = {
            "farm-100": Farm("farm-100", "Riverina Plains", Region.NSW),
        }
        self._next_number = 101

    def next_id(self) -> str:
        with self._lock:
            farm_id = f"farm-{self._next_number}"
            self._next_number += 1
            return farm_id

    def get(self, farm_id: str) -> Farm | None:
        return self._farms.get(farm_id)

    def save(self, farm: Farm) -> None:
        with self._lock:
            self._farms[farm.id] = farm

    def delete(self, farm_id: str) -> bool:
        with self._lock:
            return self._farms.pop(farm_id, None) is not None
