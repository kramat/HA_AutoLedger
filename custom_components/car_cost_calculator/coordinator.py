"""DataUpdateCoordinator for Car Cost Calculator."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_ODOMETER_ENTITY,
    CONF_FUEL_LEVEL_ENTITY,
    CONF_BATTERY_LEVEL_ENTITY,
    CONF_CHARGING_ENERGY_ENTITY,
    CONF_CHARGING_POWER_ENTITY,
)
from .store import CarCostStore

_LOGGER = logging.getLogger(__name__)

class CarCostCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Car Cost Calculator data."""

    def __init__(self, hass: HomeAssistant, entry, store: CarCostStore) -> None:
        """Initialize."""
        self.entry = entry
        self.store = store
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    def _get_entity_float(self, entity_id: str | None) -> float | None:
        """Get entity state as float."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    async def _async_update_data(self) -> dict:
        """Update data via store."""
        try:
            data = {
                "odometer": self._get_entity_float(self.entry.data.get(CONF_ODOMETER_ENTITY)),
                "fuel_level": self._get_entity_float(self.entry.data.get(CONF_FUEL_LEVEL_ENTITY)),
                "battery_level": self._get_entity_float(self.entry.data.get(CONF_BATTERY_LEVEL_ENTITY)),
                "energy": self._get_entity_float(self.entry.data.get(CONF_CHARGING_ENERGY_ENTITY)),
                "power": self._get_entity_float(self.entry.data.get(CONF_CHARGING_POWER_ENTITY)),
                "store_data": {
                    "total_energy_cost": self.store.get_total_energy_cost(),
                    "total_fuel_cost": self.store.get_total_fuel_cost(),
                    "total_maintenance_cost": self.store.get_total_maintenance_cost(),
                    "total_cost": self.store.get_total_cost(),
                    "total_distance": self.store.get_total_distance(),
                    "cost_per_km": self.store.get_cost_per_km(),
                    "session_count": self.store.get_session_count(),
                    "refuel_count": self.store.get_refuel_count(),
                    "maintenance_count": self.store.get_maintenance_count(),
                    "last_session": self.store.get_last_session(),
                }
            }
            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with store: {err}")
