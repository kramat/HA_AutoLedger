"""Constants for the Car Cost Calculator integration."""
from __future__ import annotations

DOMAIN = "car_cost_calculator"
STORAGE_VERSION = 1
STORAGE_KEY = "car_cost_calculator"

# Car types
CAR_TYPE_GAS = "gas"
CAR_TYPE_PHEV = "phev"
CAR_TYPE_EV = "ev"
CAR_TYPES = [CAR_TYPE_GAS, CAR_TYPE_PHEV, CAR_TYPE_EV]

# Config keys
CONF_CAR_NAME = "car_name"
CONF_CAR_TYPE = "car_type"
CONF_ODOMETER_ENTITY = "odometer_entity"
CONF_FUEL_LEVEL_ENTITY = "fuel_level_entity"
CONF_BATTERY_LEVEL_ENTITY = "battery_level_entity"
CONF_CHARGING_ENERGY_ENTITY = "charging_energy_entity"
CONF_CHARGING_POWER_ENTITY = "charging_power_entity"
CONF_ELECTRICITY_PRICE = "electricity_price_per_kwh"
CONF_FUEL_PRICE = "fuel_price_per_litre"
CONF_FUEL_TANK_SIZE = "fuel_tank_size_litres"
CONF_POWER_THRESHOLD = "power_threshold_watts"
CONF_DEBOUNCE_SECONDS = "debounce_seconds"

# Defaults
DEFAULT_POWER_THRESHOLD = 50  # Watts
DEFAULT_DEBOUNCE_SECONDS = 120  # 2 minutes
DEFAULT_ELECTRICITY_PRICE = 0.30  # EUR/kWh
DEFAULT_FUEL_PRICE = 1.80  # EUR/litre
DEFAULT_FUEL_TANK_SIZE = 50.0  # litres

CURRENCY = "EUR"
CURRENCY_SYMBOL = "€"

# Services
SERVICE_ADD_REFUEL = "add_refuel"
SERVICE_ADD_CHARGE = "add_charge"
SERVICE_ADD_MAINTENANCE = "add_maintenance"
SERVICE_DELETE_ENTRY = "delete_entry"
SERVICE_EXPORT_DATA = "export_data"

# Session types
SESSION_TYPE_CHARGE = "charge"
SESSION_TYPE_REFUEL = "refuel"
SESSION_SOURCE_AUTO = "auto"
SESSION_SOURCE_MANUAL = "manual"

# Entry types for storage
ENTRY_TYPE_SESSION = "session"
ENTRY_TYPE_MAINTENANCE = "maintenance"

# Events
EVENT_SESSION_COMPLETED = f"{DOMAIN}_session_completed"
EVENT_REFUEL_ADDED = f"{DOMAIN}_refuel_added"
EVENT_MAINTENANCE_ADDED = f"{DOMAIN}_maintenance_added"

# Platforms
PLATFORMS = ["sensor"]

# Export formats
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_JSON = "json"
EXPORT_FORMATS = [EXPORT_FORMAT_CSV, EXPORT_FORMAT_JSON]
