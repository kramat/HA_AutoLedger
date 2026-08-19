"""Session monitor for Car Cost Calculator."""
from datetime import datetime
from enum import Enum
import logging
from typing import Any
import uuid

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util.dt import utcnow

from .const import (
    CONF_CHARGING_POWER_ENTITY,
    CONF_DEBOUNCE_SECONDS,
    CONF_ELECTRICITY_PRICE,
    CONF_FUEL_TANK_SIZE,
    CONF_POWER_THRESHOLD,
    DEFAULT_DEBOUNCE_SECONDS,
    DEFAULT_POWER_THRESHOLD,
    EVENT_SESSION_COMPLETED,
    SESSION_SOURCE_AUTO,
    SESSION_TYPE_CHARGE,
)

_LOGGER = logging.getLogger(__name__)


class ChargingState(Enum):
    """Charging states."""
    IDLE = "idle"
    CHARGING = "charging"
    FINALISING = "finalising"


class ChargingSessionMonitor:
    """Monitor charging sessions."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: Any,
        store: Any,
        coordinator: Any,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.entry = entry
        self.store = store
        self.coordinator = coordinator
        self._state = ChargingState.IDLE
        self._unsub_state = None
        self._unsub_timer = None

        self._power_entity = self.entry.data.get(CONF_CHARGING_POWER_ENTITY)
        self._power_threshold = self.entry.data.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD)
        self._debounce_seconds = self.entry.data.get(CONF_DEBOUNCE_SECONDS, DEFAULT_DEBOUNCE_SECONDS)

        self._session_start_data: dict[str, Any] = {}

    async def async_start(self) -> None:
        """Start monitoring."""
        if not self._power_entity:
            return
        self._unsub_state = async_track_state_change_event(
            self.hass, self._power_entity, self._handle_power_change
        )

    async def async_stop(self) -> None:
        """Stop monitoring."""
        if self._unsub_state:
            self._unsub_state()
            self._unsub_state = None
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    @callback
    def _handle_power_change(self, event: Event[EventStateChangedData]) -> None:
        """Handle power entity state change."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ("unknown", "unavailable"):
            return

        try:
            power = float(new_state.state)
        except ValueError:
            return

        if self._state == ChargingState.IDLE:
            if power > self._power_threshold:
                self._start_session()
        elif self._state == ChargingState.CHARGING:
            if power < self._power_threshold:
                self._state = ChargingState.FINALISING
                self._unsub_timer = async_call_later(
                    self.hass, self._debounce_seconds, self._finish_session
                )
        elif self._state == ChargingState.FINALISING:
            if power > self._power_threshold:
                if self._unsub_timer:
                    self._unsub_timer()
                    self._unsub_timer = None
                self._state = ChargingState.CHARGING

    def _start_session(self) -> None:
        """Start a charging session."""
        self._state = ChargingState.CHARGING
        self._session_start_data = {
            "timestamp_start": utcnow().isoformat(),
            "odometer": self.coordinator.data.get("odometer"),
            "fuel_level": self.coordinator.data.get("fuel_level"),
            "battery_level": self.coordinator.data.get("battery_level"),
            "energy": self.coordinator.data.get("energy"),
        }
        _LOGGER.debug("Started charging session")

    async def _finish_session(self, now: datetime) -> None:
        """Finish a charging session."""
        self._state = ChargingState.IDLE
        self._unsub_timer = None

        timestamp_end = utcnow().isoformat()
        odometer_end = self.coordinator.data.get("odometer")
        fuel_level_end = self.coordinator.data.get("fuel_level")
        battery_level_end = self.coordinator.data.get("battery_level")
        energy_end = self.coordinator.data.get("energy")

        odometer_start = self._session_start_data.get("odometer")
        fuel_level_start = self._session_start_data.get("fuel_level")
        battery_level_start = self._session_start_data.get("battery_level")
        energy_start = self._session_start_data.get("energy")

        energy_kwh = None
        if energy_start is not None and energy_end is not None:
            try:
                energy_kwh = max(0.0, float(energy_end) - float(energy_start))
            except ValueError:
                energy_kwh = None

        distance_km = None
        if odometer_start is not None and odometer_end is not None:
            try:
                distance_km = max(0.0, float(odometer_end) - float(odometer_start))
            except ValueError:
                distance_km = None

        electricity_price = float(self.entry.data.get(CONF_ELECTRICITY_PRICE, 0.0))
        cost = (energy_kwh or 0.0) * electricity_price

        litres = None
        if fuel_level_start is not None and fuel_level_end is not None:
            try:
                fuel_level_start_fl = float(fuel_level_start)
                fuel_level_end_fl = float(fuel_level_end)
                tank_size = float(self.entry.data.get(CONF_FUEL_TANK_SIZE, 0.0))
                if fuel_level_start_fl > fuel_level_end_fl and tank_size > 0:
                    litres = (fuel_level_start_fl - fuel_level_end_fl) / 100.0 * tank_size
            except ValueError:
                litres = None

        session = {
            "id": str(uuid.uuid4()),
            "type": SESSION_TYPE_CHARGE,
            "source": SESSION_SOURCE_AUTO,
            "timestamp_start": self._session_start_data.get("timestamp_start"),
            "timestamp_end": timestamp_end,
            "energy_kwh": energy_kwh,
            "cost": cost,
            "price_per_unit": electricity_price,
            "odometer_start_km": float(odometer_start) if odometer_start is not None else None,
            "odometer_end_km": float(odometer_end) if odometer_end is not None else None,
            "distance_km": distance_km,
            "fuel_level_start_pct": float(fuel_level_start) if fuel_level_start is not None else None,
            "fuel_level_end_pct": float(fuel_level_end) if fuel_level_end is not None else None,
            "battery_level_start_pct": float(battery_level_start) if battery_level_start is not None else None,
            "battery_level_end_pct": float(battery_level_end) if battery_level_end is not None else None,
            "litres": litres,
            "notes": "Auto-detected charging session",
        }

        await self.store.async_add_session(session)
        self.hass.bus.async_fire(EVENT_SESSION_COMPLETED, session)
        await self.coordinator.async_request_refresh()
        _LOGGER.debug("Finished charging session")
