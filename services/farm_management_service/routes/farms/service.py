"""Farm use cases: register, read, update and delete farm records.

Each change publishes a farm event so services that keep local farm references
(Telemetry, Irrigation control, AI decision) can update them (ADR 07).
"""

from __future__ import annotations

from services.farm_management_service.domain.models import Farm, Region
from services.farm_management_service.infrastructure.farm_repository import InMemoryFarmRepository
from services.shared.errors import not_found
from services.shared.events import DomainEvent, EventPublisher

SOURCE = "farm-management-service"


class FarmService:
    def __init__(self, repository: InMemoryFarmRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    def get_farm(self, farm_id: str) -> Farm:
        farm = self._repository.get(farm_id)
        if farm is None:
            raise not_found("Farm", farm_id)
        return farm

    def register_farm(self, name: str, region: Region) -> Farm:
        farm = Farm(id=self._repository.next_id(), name=name, region=region)
        self._repository.save(farm)
        self._publish("FarmRegistered", farm)
        return farm

    def update_farm(self, farm_id: str, name: str, region: Region) -> Farm:
        farm = self.get_farm(farm_id)
        farm.name = name
        farm.region = region
        self._repository.save(farm)
        self._publish("FarmUpdated", farm)
        return farm

    def delete_farm(self, farm_id: str) -> None:
        if not self._repository.delete(farm_id):
            raise not_found("Farm", farm_id)
        self._publisher.publish(DomainEvent("FarmDeleted", SOURCE, {"farmId": farm_id}))

    def _publish(self, event_type: str, farm: Farm) -> None:
        self._publisher.publish(
            DomainEvent(event_type, SOURCE, {"farmId": farm.id, "name": farm.name, "region": farm.region.value})
        )
