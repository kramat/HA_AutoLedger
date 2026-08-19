"""Config flow for Car Cost Calculator integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CAR_TYPE_GAS,
    CAR_TYPE_PHEV,
    CAR_TYPE_EV,
    CONF_CAR_NAME,
    CONF_CAR_TYPE,
    CONF_ODOMETER_ENTITY,
    CONF_FUEL_LEVEL_ENTITY,
    CONF_BATTERY_LEVEL_ENTITY,
    CONF_CHARGING_ENERGY_ENTITY,
    CONF_CHARGING_POWER_ENTITY,
    CONF_ELECTRICITY_PRICE,
    CONF_FUEL_PRICE,
    CONF_FUEL_TANK_SIZE,
    CONF_POWER_THRESHOLD,
    CONF_DEBOUNCE_SECONDS,
    DEFAULT_POWER_THRESHOLD,
    DEFAULT_DEBOUNCE_SECONDS,
    DEFAULT_ELECTRICITY_PRICE,
    DEFAULT_FUEL_PRICE,
    DEFAULT_FUEL_TANK_SIZE,
)

_LOGGER = logging.getLogger(__name__)

class CarCostConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Car Cost Calculator."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAR_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_CAR_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=CAR_TYPE_GAS, label="Gas / Petrol"),
                                selector.SelectOptionDict(value=CAR_TYPE_PHEV, label="Plug-in Hybrid (PHEV)"),
                                selector.SelectOptionDict(value=CAR_TYPE_EV, label="Electric (EV)"),
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the entities step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pricing()

        car_type = self._data[CONF_CAR_TYPE]
        schema: dict[vol.Marker, Any] = {
            vol.Required(CONF_ODOMETER_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        }

        if car_type in [CAR_TYPE_GAS, CAR_TYPE_PHEV]:
            schema[vol.Required(CONF_FUEL_LEVEL_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )

        if car_type in [CAR_TYPE_EV, CAR_TYPE_PHEV]:
            schema[vol.Required(CONF_BATTERY_LEVEL_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
            schema[vol.Required(CONF_CHARGING_ENERGY_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
            schema[vol.Required(CONF_CHARGING_POWER_ENTITY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )

        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_pricing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the pricing step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data[CONF_CAR_NAME], data=self._data
            )

        car_type = self._data[CONF_CAR_TYPE]
        schema: dict[vol.Marker, Any] = {}

        if car_type in [CAR_TYPE_EV, CAR_TYPE_PHEV]:
            schema[vol.Required(CONF_ELECTRICITY_PRICE, default=DEFAULT_ELECTRICITY_PRICE)] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )
            schema[vol.Required(CONF_POWER_THRESHOLD, default=DEFAULT_POWER_THRESHOLD)] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )
            schema[vol.Required(CONF_DEBOUNCE_SECONDS, default=DEFAULT_DEBOUNCE_SECONDS)] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=1)
            )

        if car_type in [CAR_TYPE_GAS, CAR_TYPE_PHEV]:
            schema[vol.Required(CONF_FUEL_PRICE, default=DEFAULT_FUEL_PRICE)] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )
            schema[vol.Required(CONF_FUEL_TANK_SIZE, default=DEFAULT_FUEL_TANK_SIZE)] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )

        return self.async_show_form(
            step_id="pricing",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return CarCostOptionsFlow(config_entry)


class CarCostOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Car Cost Calculator."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._data = dict(config_entry.data)
        self._data.update(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CAR_NAME, default=self._data.get(CONF_CAR_NAME, "")
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(
                        CONF_CAR_TYPE, default=self._data.get(CONF_CAR_TYPE, CAR_TYPE_GAS)
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=CAR_TYPE_GAS, label="Gas / Petrol"),
                                selector.SelectOptionDict(value=CAR_TYPE_PHEV, label="Plug-in Hybrid (PHEV)"),
                                selector.SelectOptionDict(value=CAR_TYPE_EV, label="Electric (EV)"),
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the entities step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_pricing()

        car_type = self._data[CONF_CAR_TYPE]
        schema: dict[vol.Marker, Any] = {
            vol.Required(
                CONF_ODOMETER_ENTITY, default=self._data.get(CONF_ODOMETER_ENTITY, "")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        }

        if car_type in [CAR_TYPE_GAS, CAR_TYPE_PHEV]:
            schema[vol.Required(
                CONF_FUEL_LEVEL_ENTITY, default=self._data.get(CONF_FUEL_LEVEL_ENTITY, "")
            )] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )

        if car_type in [CAR_TYPE_EV, CAR_TYPE_PHEV]:
            schema[vol.Required(
                CONF_BATTERY_LEVEL_ENTITY, default=self._data.get(CONF_BATTERY_LEVEL_ENTITY, "")
            )] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
            schema[vol.Required(
                CONF_CHARGING_ENERGY_ENTITY, default=self._data.get(CONF_CHARGING_ENERGY_ENTITY, "")
            )] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
            schema[vol.Required(
                CONF_CHARGING_POWER_ENTITY, default=self._data.get(CONF_CHARGING_POWER_ENTITY, "")
            )] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )

        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_pricing(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the pricing step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title="", data=self._data
            )

        car_type = self._data[CONF_CAR_TYPE]
        schema: dict[vol.Marker, Any] = {}

        if car_type in [CAR_TYPE_EV, CAR_TYPE_PHEV]:
            schema[vol.Required(
                CONF_ELECTRICITY_PRICE,
                default=self._data.get(CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE)
            )] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )
            schema[vol.Required(
                CONF_POWER_THRESHOLD,
                default=self._data.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD)
            )] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )
            schema[vol.Required(
                CONF_DEBOUNCE_SECONDS,
                default=self._data.get(CONF_DEBOUNCE_SECONDS, DEFAULT_DEBOUNCE_SECONDS)
            )] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step=1)
            )

        if car_type in [CAR_TYPE_GAS, CAR_TYPE_PHEV]:
            schema[vol.Required(
                CONF_FUEL_PRICE,
                default=self._data.get(CONF_FUEL_PRICE, DEFAULT_FUEL_PRICE)
            )] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )
            schema[vol.Required(
                CONF_FUEL_TANK_SIZE,
                default=self._data.get(CONF_FUEL_TANK_SIZE, DEFAULT_FUEL_TANK_SIZE)
            )] = selector.NumberSelector(
                selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
            )

        return self.async_show_form(
            step_id="pricing",
            data_schema=vol.Schema(schema),
            errors=errors,
        )
