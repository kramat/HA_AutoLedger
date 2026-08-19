"""Sensor platform for Car Cost Calculator."""
from dataclasses import dataclass
from typing import Any, Callable
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CAR_TYPE_GAS,
    CAR_TYPE_PHEV,
    CAR_TYPE_EV,
    CONF_CAR_NAME,
    CONF_CAR_TYPE,
    CURRENCY_SYMBOL,
)
from .coordinator import CarCostCoordinator

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True, kw_only=True)
class CarCostSensorEntityDescription(SensorEntityDescription):
    """Class describing Car Cost Calculator sensor entities."""
    value_fn: Callable[[dict], Any] | None = None

SENSORS: tuple[CarCostSensorEntityDescription, ...] = (
    CarCostSensorEntityDescription(
        key="total_energy_cost",
        name="Total Energy Cost",
        native_unit_of_measurement=CURRENCY_SYMBOL,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data["store_data"]["total_energy_cost"],
    ),
    CarCostSensorEntityDescription(
        key="total_fuel_cost",
        name="Total Fuel Cost",
        native_unit_of_measurement=CURRENCY_SYMBOL,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data["store_data"]["total_fuel_cost"],
    ),
    CarCostSensorEntityDescription(
        key="total_maintenance_cost",
        name="Total Maintenance Cost",
        native_unit_of_measurement=CURRENCY_SYMBOL,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data["store_data"]["total_maintenance_cost"],
    ),
    CarCostSensorEntityDescription(
        key="total_cost",
        name="Total Cost",
        native_unit_of_measurement=CURRENCY_SYMBOL,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data["store_data"]["total_cost"],
    ),
    CarCostSensorEntityDescription(
        key="total_distance",
        name="Total Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["store_data"]["total_distance"],
    ),
    CarCostSensorEntityDescription(
        key="cost_per_km",
        name="Cost per Kilometer",
        native_unit_of_measurement=f"{CURRENCY_SYMBOL}/{UnitOfLength.KILOMETERS}",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["store_data"]["cost_per_km"],
    ),
    CarCostSensorEntityDescription(
        key="last_session_energy",
        name="Last Session Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["store_data"]["last_session"].get("energy_kwh") if data["store_data"]["last_session"] else None,
    ),
    CarCostSensorEntityDescription(
        key="last_session_cost",
        name="Last Session Cost",
        native_unit_of_measurement=CURRENCY_SYMBOL,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["store_data"]["last_session"].get("cost") if data["store_data"]["last_session"] else None,
    ),
    CarCostSensorEntityDescription(
        key="last_session_distance",
        name="Last Session Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data["store_data"]["last_session"].get("distance_km") if data["store_data"]["last_session"] else None,
    ),
    CarCostSensorEntityDescription(
        key="charging_sessions_count",
        name="Charging Sessions",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["store_data"]["session_count"],
    ),
    CarCostSensorEntityDescription(
        key="refuels_count",
        name="Refuels",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["store_data"]["refuel_count"],
    ),
    CarCostSensorEntityDescription(
        key="maintenance_count",
        name="Maintenance Entries",
        native_unit_of_measurement=None,
        device_class=None,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data["store_data"]["maintenance_count"],
    ),
)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    car_type = entry.data.get(CONF_CAR_TYPE, CAR_TYPE_GAS)
    
    entities = []
    for description in SENSORS:
        # Filter sensors based on car_type (skip fuel sensors for EV, skip energy sensors for gas-only)
        if car_type == CAR_TYPE_EV and description.key in ("total_fuel_cost", "refuels_count"):
            continue
        if car_type == CAR_TYPE_GAS and description.key in ("total_energy_cost", "last_session_energy", "charging_sessions_count"):
            continue
            
        entities.append(CarCostSensor(coordinator, entry, description))
        
    async_add_entities(entities)

class CarCostSensor(CoordinatorEntity[CarCostCoordinator], SensorEntity):
    """Car Cost Calculator Sensor."""
    
    entity_description: CarCostSensorEntityDescription
    
    def __init__(self, coordinator: CarCostCoordinator, entry, description: CarCostSensorEntityDescription) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        car_name = entry.data.get(CONF_CAR_NAME, "Car")
        self._attr_name = f"{car_name} {description.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=car_name,
            manufacturer="Car Cost Calculator",
        )
        
    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        val = self.entity_description.value_fn(self.coordinator.data)
        if val is None:
            return None
        if self.entity_description.device_class == SensorDeviceClass.MONETARY:
            return round(float(val), 2)
        if self.entity_description.device_class == SensorDeviceClass.DISTANCE:
            return round(float(val), 1)
        return val
