"""Data store for Car Cost Calculator."""
import logging
from typing import Any
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    SESSION_TYPE_CHARGE,
    SESSION_TYPE_REFUEL,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_DATA = {
    "sessions": [],
    "maintenance": [],
}


class CarCostStore:
    """Store for Car Cost Calculator data."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the store."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry_id}")
        self._data: dict[str, list[dict[str, Any]]] = DEFAULT_DATA.copy()

    async def async_load(self) -> dict[str, Any]:
        """Load data from storage."""
        data = await self._store.async_load()
        if data is None:
            self._data = DEFAULT_DATA.copy()
        else:
            self._data = data
        return self._data

    async def async_save(self, data: dict[str, Any]) -> None:
        """Save data to storage."""
        self._data = data
        await self._store.async_save(data)

    async def async_add_session(self, session: dict[str, Any]) -> None:
        """Add a session and save."""
        if "id" not in session:
            session["id"] = str(uuid.uuid4())
        self._data.setdefault("sessions", []).append(session)
        await self.async_save(self._data)

    async def async_add_maintenance(self, entry: dict[str, Any]) -> None:
        """Add a maintenance entry and save."""
        if "id" not in entry:
            entry["id"] = str(uuid.uuid4())
        self._data.setdefault("maintenance", []).append(entry)
        await self.async_save(self._data)

    async def async_delete_entry(self, entry_id: str) -> bool:
        """Delete an entry by ID."""
        for i, session in enumerate(self._data.get("sessions", [])):
            if session.get("id") == entry_id:
                self._data["sessions"].pop(i)
                await self.async_save(self._data)
                return True
        for i, entry in enumerate(self._data.get("maintenance", [])):
            if entry.get("id") == entry_id:
                self._data["maintenance"].pop(i)
                await self.async_save(self._data)
                return True
        return False

    async def async_get_sessions(self) -> list[dict[str, Any]]:
        """Get all sessions."""
        return self._data.get("sessions", [])

    async def async_get_maintenance(self) -> list[dict[str, Any]]:
        """Get all maintenance entries."""
        return self._data.get("maintenance", [])

    async def async_get_all_data(self) -> dict[str, Any]:
        """Get all data."""
        return self._data

    def get_total_energy_cost(self) -> float:
        """Get total energy cost."""
        return sum(
            session.get("cost", 0.0)
            for session in self._data.get("sessions", [])
            if session.get("type") == SESSION_TYPE_CHARGE
        )

    def get_total_fuel_cost(self) -> float:
        """Get total fuel cost."""
        return sum(
            session.get("cost", 0.0)
            for session in self._data.get("sessions", [])
            if session.get("type") == SESSION_TYPE_REFUEL
        )

    def get_total_maintenance_cost(self) -> float:
        """Get total maintenance cost."""
        return sum(entry.get("cost", 0.0) for entry in self._data.get("maintenance", []))

    def get_total_cost(self) -> float:
        """Get total cost."""
        return (
            self.get_total_energy_cost()
            + self.get_total_fuel_cost()
            + self.get_total_maintenance_cost()
        )

    def get_total_distance(self) -> float:
        """Get total distance."""
        return sum(session.get("distance_km", 0.0) or 0.0 for session in self._data.get("sessions", []))

    def get_cost_per_km(self) -> float:
        """Get cost per km."""
        distance = self.get_total_distance()
        if distance > 0:
            return self.get_total_cost() / distance
        return 0.0

    def get_session_count(self) -> int:
        """Get session count."""
        return len([s for s in self._data.get("sessions", []) if s.get("type") == SESSION_TYPE_CHARGE])

    def get_refuel_count(self) -> int:
        """Get refuel count."""
        return len([s for s in self._data.get("sessions", []) if s.get("type") == SESSION_TYPE_REFUEL])

    def get_maintenance_count(self) -> int:
        """Get maintenance count."""
        return len(self._data.get("maintenance", []))

    def get_last_session(self) -> dict[str, Any] | None:
        """Get last session."""
        sessions = self._data.get("sessions", [])
        if sessions:
            return sessions[-1]
        return None
