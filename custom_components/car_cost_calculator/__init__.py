"""The Car Cost Calculator integration."""
import csv
import json
import logging
from datetime import datetime
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_CAR_TYPE,
    CAR_TYPE_GAS,
    CAR_TYPE_PHEV,
    CAR_TYPE_EV,
    SERVICE_ADD_REFUEL,
    SERVICE_ADD_CHARGE,
    SERVICE_ADD_MAINTENANCE,
    SERVICE_DELETE_ENTRY,
    SERVICE_EXPORT_DATA,
    EVENT_SESSION_COMPLETED,
    EVENT_REFUEL_ADDED,
    EVENT_MAINTENANCE_ADDED,
)
from .coordinator import CarCostCoordinator
from .store import CarCostStore
from .session_monitor import ChargingSessionMonitor

_LOGGER = logging.getLogger(__name__)

SCHEMA_ADD_REFUEL = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required("litres"): vol.Coerce(float),
    vol.Optional("price_total"): vol.Coerce(float),
    vol.Optional("price_per_litre"): vol.Coerce(float),
    vol.Optional("odometer_km"): vol.Coerce(float),
    vol.Optional("is_full_tank", default=False): cv.boolean,
    vol.Optional("notes", default=""): cv.string,
})

SCHEMA_ADD_CHARGE = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required("energy_kwh"): vol.Coerce(float),
    vol.Optional("price_total"): vol.Coerce(float),
    vol.Optional("price_per_kwh"): vol.Coerce(float),
    vol.Optional("odometer_km"): vol.Coerce(float),
    vol.Optional("notes", default=""): cv.string,
})

SCHEMA_ADD_MAINTENANCE = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required("description"): cv.string,
    vol.Required("cost"): vol.Coerce(float),
    vol.Optional("odometer_km"): vol.Coerce(float),
    vol.Optional("date"): cv.string,
    vol.Optional("notes", default=""): cv.string,
})

SCHEMA_DELETE_ENTRY = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Required("record_id"): cv.string,
})

SCHEMA_EXPORT_DATA = vol.Schema({
    vol.Required("entry_id"): cv.string,
    vol.Optional("format", default="csv"): vol.In(["csv", "json"]),
})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Car Cost Calculator component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up Car Cost Calculator from a config entry."""
    store = CarCostStore(hass, entry.entry_id)
    await store.async_load()

    coordinator = CarCostCoordinator(hass, entry, store)
    await coordinator.async_config_entry_first_refresh()

    monitor = None
    car_type = entry.data.get(CONF_CAR_TYPE, CAR_TYPE_GAS)
    if car_type in (CAR_TYPE_PHEV, CAR_TYPE_EV):
        monitor = ChargingSessionMonitor(hass, entry, store, coordinator)
        await monitor.async_start()

    hass.data[DOMAIN][entry.entry_id] = {
        "store": store,
        "coordinator": coordinator,
        "monitor": monitor,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_ADD_REFUEL):
        _register_services(hass)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    monitor = data.get("monitor")
    if monitor:
        await monitor.async_stop()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def _register_services(hass: HomeAssistant):
    """Register custom services."""
    
    async def handle_add_refuel(call: ServiceCall):
        entry_id = call.data["entry_id"]
        if entry_id not in hass.data[DOMAIN]:
            return
        store: CarCostStore = hass.data[DOMAIN][entry_id]["store"]
        coordinator: CarCostCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        
        litres = call.data["litres"]
        price_total = call.data.get("price_total")
        price_per_litre = call.data.get("price_per_litre")

        # Calculate cost: prefer price_total, otherwise litres × price_per_litre
        if price_total is not None:
            cost = float(price_total)
        elif price_per_litre is not None:
            cost = litres * float(price_per_litre)
        else:
            cost = 0.0

        session = {
            "type": "refuel",
            "source": "manual",
            "litres": litres,
            "cost": cost,
            "price_per_unit": price_per_litre,
            "odometer_end_km": call.data.get("odometer_km"),
            "is_full_tank": call.data.get("is_full_tank", False),
            "notes": call.data.get("notes", ""),
            "timestamp_end": datetime.now().isoformat(),
        }
        await store.async_add_session(session)
        hass.bus.async_fire(EVENT_REFUEL_ADDED, {"entry_id": entry_id, **session})
        await coordinator.async_request_refresh()

    async def handle_add_charge(call: ServiceCall):
        entry_id = call.data["entry_id"]
        if entry_id not in hass.data[DOMAIN]:
            return
        store: CarCostStore = hass.data[DOMAIN][entry_id]["store"]
        coordinator: CarCostCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        
        energy_kwh = call.data["energy_kwh"]
        price_total = call.data.get("price_total")
        price_per_kwh = call.data.get("price_per_kwh")

        # Calculate cost: prefer price_total, otherwise energy × price_per_kwh
        if price_total is not None:
            cost = float(price_total)
        elif price_per_kwh is not None:
            cost = energy_kwh * float(price_per_kwh)
        else:
            cost = 0.0

        session = {
            "type": "charge",
            "source": "manual",
            "energy_kwh": energy_kwh,
            "cost": cost,
            "price_per_unit": price_per_kwh,
            "odometer_end_km": call.data.get("odometer_km"),
            "notes": call.data.get("notes", ""),
            "timestamp_end": datetime.now().isoformat(),
        }
        await store.async_add_session(session)
        hass.bus.async_fire(EVENT_SESSION_COMPLETED, {"entry_id": entry_id, **session})
        await coordinator.async_request_refresh()

    async def handle_add_maintenance(call: ServiceCall):
        entry_id = call.data["entry_id"]
        if entry_id not in hass.data[DOMAIN]:
            return
        store: CarCostStore = hass.data[DOMAIN][entry_id]["store"]
        coordinator: CarCostCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        
        record = {
            "description": call.data["description"],
            "cost": call.data["cost"],
            "odometer_km": call.data.get("odometer_km"),
            "date": call.data.get("date", datetime.now().isoformat()),
            "notes": call.data.get("notes", ""),
        }
        await store.async_add_maintenance(record)
        hass.bus.async_fire(EVENT_MAINTENANCE_ADDED, {"entry_id": entry_id, **record})
        await coordinator.async_request_refresh()

    async def handle_delete_entry(call: ServiceCall):
        entry_id = call.data["entry_id"]
        if entry_id not in hass.data[DOMAIN]:
            return
        store: CarCostStore = hass.data[DOMAIN][entry_id]["store"]
        coordinator: CarCostCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        
        await store.async_delete_entry(call.data["record_id"])
        await coordinator.async_request_refresh()

    async def handle_export_data(call: ServiceCall):
        entry_id = call.data["entry_id"]
        if entry_id not in hass.data[DOMAIN]:
            return
        store: CarCostStore = hass.data[DOMAIN][entry_id]["store"]
        
        export_format = call.data.get("format", "csv")
        data = await store.async_get_all_data()
        
        file_path = hass.config.path(f"car_cost_calculator_export_{entry_id}.{export_format}")
        
        def write_file():
            if export_format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            else:
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["--- SESSIONS ---"])
                    if data.get("sessions"):
                        keys = list(data["sessions"][0].keys())
                        writer.writerow(keys)
                        for session in data["sessions"]:
                            writer.writerow([session.get(k, "") for k in keys])
                            
                    writer.writerow([])
                    writer.writerow(["--- MAINTENANCE ---"])
                    if data.get("maintenance"):
                        keys = list(data["maintenance"][0].keys())
                        writer.writerow(keys)
                        for maint in data["maintenance"]:
                            writer.writerow([maint.get(k, "") for k in keys])

        await hass.async_add_executor_job(write_file)
        hass.components.persistent_notification.async_create(
            f"Data exported successfully to: {file_path}",
            title="Car Cost Calculator Export",
        )

    hass.services.async_register(DOMAIN, SERVICE_ADD_REFUEL, handle_add_refuel, schema=SCHEMA_ADD_REFUEL)
    hass.services.async_register(DOMAIN, SERVICE_ADD_CHARGE, handle_add_charge, schema=SCHEMA_ADD_CHARGE)
    hass.services.async_register(DOMAIN, SERVICE_ADD_MAINTENANCE, handle_add_maintenance, schema=SCHEMA_ADD_MAINTENANCE)
    hass.services.async_register(DOMAIN, SERVICE_DELETE_ENTRY, handle_delete_entry, schema=SCHEMA_DELETE_ENTRY)
    hass.services.async_register(DOMAIN, SERVICE_EXPORT_DATA, handle_export_data, schema=SCHEMA_EXPORT_DATA)
