# Car Cost Calculator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1.0+-blue.svg?style=for-the-badge)](https://www.home-assistant.io/)

A comprehensive Home Assistant integration to track and calculate the driving and ownership costs of your vehicles. Supports Gas, EV, and PHEV cars.

## Features
- **Multi-car tracking**: Track multiple vehicles independently in one integration.
- **Gas, PHEV, and EV support**: Full support for all modern vehicle types.
- **Auto charging detection**: Detects EV/PHEV charging sessions automatically using a power threshold (e.g., Shelly relays or smart plugs).
- **Manual refuel/charge entry**: Log your manual refuels and charges to keep accurate records.
- **Maintenance logging**: Keep track of maintenance events and costs (e.g., service, tires, insurance).
- **Cost calculation**: Real-time sensors calculating cost per 100km, total cost, etc.
- **Data export**: Export your data to CSV or JSON formats for external analysis.

## Installation

### HACS (Recommended)
1. Open HACS in your Home Assistant instance.
2. Click on `Integrations`.
3. Click the 3 dots in the top right corner and select `Custom repositories`.
4. Add the repository URL and select `Integration` as the category.
5. Search for "Car Cost Calculator" and click Download.
6. Restart Home Assistant.

### Manual
1. Copy the `custom_components/car_cost_calculator` folder to your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings -> Devices & Services**.
2. Click **Add Integration** and search for "Car Cost Calculator".
3. Follow the UI setup process.
   - *[Placeholder for Screenshot 1: Setup Wizard]*
   - Enter your car's name, type (Gas/EV/PHEV).
   - Select the odometer and optional fuel/battery entities.
   - Configure pricing and auto-charging thresholds if applicable.
   - *[Placeholder for Screenshot 2: Entity Selection]*

## Entities

For each configured car, the integration provides several sensors:

| Entity | Description |
|---|---|
| `sensor.[car_name]_total_cost` | Total cumulative cost of ownership |
| `sensor.[car_name]_cost_per_100km` | Calculated cost per 100km / 100mi |
| `sensor.[car_name]_total_fuel_cost` | Total cost spent on liquid fuel |
| `sensor.[car_name]_total_charging_cost` | Total cost spent on electricity |
| `sensor.[car_name]_total_maintenance_cost`| Total cost of maintenance |
| `sensor.[car_name]_last_refuel_date` | Date of the last recorded refuel |
| `sensor.[car_name]_last_charge_date` | Date of the last recorded charge |

## Services

### `car_cost_calculator.add_refuel`
Add a manual refuel entry.
```yaml
service: car_cost_calculator.add_refuel
data:
  car: "My Car"
  litres: 45.2
  cost: 75.50
  odometer: 125000
```

### `car_cost_calculator.add_charge`
Add a manual charging session.
```yaml
service: car_cost_calculator.add_charge
data:
  car: "My EV"
  kwh: 40.5
  cost: 12.15
  odometer: 45000
```

### `car_cost_calculator.add_maintenance`
Add a maintenance log.
```yaml
service: car_cost_calculator.add_maintenance
data:
  car: "My Car"
  type: "Service"
  cost: 350.00
  notes: "Oil change and filter"
```

### `car_cost_calculator.delete_entry`
Delete an accidental entry by ID.
```yaml
service: car_cost_calculator.delete_entry
data:
  car: "My Car"
  entry_id: "entry_12345"
```

### `car_cost_calculator.export_data`
Export data to a file.
```yaml
service: car_cost_calculator.export_data
data:
  car: "My Car"
  format: "csv"
```

## How Auto-Charging Detection Works
If configured, the integration monitors a power sensor (e.g., from a smart plug). When the power exceeds the `power_threshold_watts` for the `debounce_seconds`, a charging session begins. When the power drops below the threshold for the debounce period, the session ends, and the total energy consumed (from the energy sensor) is calculated and logged automatically.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)
