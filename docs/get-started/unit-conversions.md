# Unit Conversions in Stravalib

Stravalib uses the [Pint library](https://pypi.org/project/Pint/) for unit conversions, making it easy to work with Strava's metric data in your preferred units.

## Quick Start

The `stravalib.unit_helper` module provides convenient conversion functions:

```python
from stravalib import unithelper as uh

# Distance conversions
distance_meters = 5000  # Strava returns distance in meters
uh.miles(distance_meters)  # <Quantity(3.10686, 'mile')>
uh.kilometers(distance_meters)  # <Quantity(5.0, 'kilometer')>
uh.feet(distance_meters)  # <Quantity(16404.2, 'foot')>

# Speed conversions
speed_mps = 3.5  # Strava returns speed in meters/second
uh.mph(speed_mps)  # <Quantity(7.83, 'mile/hour')>
uh.kph(speed_mps)  # <Quantity(12.6, 'kilometer/hour')>

# Weight conversions
weight_kg = 70  # Strava returns weight in kilograms
uh.pounds(weight_kg)  # <Quantity(154.324, 'pound')>

# Temperature conversions
temp_c = 20  # Strava returns temperature in Celsius
uh.c2f(temp_c)  # 68.0 (Fahrenheit)
```

## Working with Activity Data

When you fetch activities from Strava, many fields come with units attached:

```python
from stravalib.client import Client

client = Client(access_token="your_token")
activity = client.get_activity(123456789)

# Distance (returned in meters)
print(activity.distance)  # 5000.0
print(uh.miles(activity.distance))  # <Quantity(3.10686, 'mile')>
print(uh.kilometers(activity.distance))  # <Quantity(5.0, 'kilometer')>

# Speed (returned in meters/second)
print(activity.average_speed)  # 3.5
print(uh.mph(activity.average_speed))  # <Quantity(7.83, 'mile/hour')>
print(uh.kph(activity.average_speed))  # <Quantity(12.6, 'kilometer/hour')>

# Elevation (returned in meters)
print(activity.total_elevation_gain)  # 150.0
print(uh.feet(activity.total_elevation_gain))  # <Quantity(492.126, 'foot')>
```

## Available Conversion Functions

### Distance
- `meter(s)` - Convert to meters
- `kilometer(s)` - Convert to kilometers
- `mile(s)` - Convert to miles
- `foot/feet` - Convert to feet

### Speed
- `meters_per_second` - Convert to m/s
- `mph` or `miles_per_hour` - Convert to miles per hour
- `kph` or `kilometers_per_hour` - Convert to kilometers per hour

### Weight
- `kilogram(s)` or `kg(s)` - Convert to kilograms
- `pound(s)` or `lb(s)` - Convert to pounds

### Time
- `second(s)` - Convert to seconds
- `hour(s)` - Convert to hours

### Temperature
- `c2f(celsius)` - Convert Celsius to Fahrenheit

## Using Pint Directly

For more advanced conversions, you can use Pint directly:

```python
from stravalib.unit_registry import ureg

# Create quantities
distance = ureg.Quantity(5000, "meter")
speed = ureg.Quantity(3.5, "meter/second")

# Convert to any unit
distance.to("mile")  # <Quantity(3.10686, 'mile')>
distance.to("yard")  # <Quantity(5468.07, 'yard')>
speed.to("kilometer/hour")  # <Quantity(12.6, 'kilometer/hour')>
speed.to("mile/hour")  # <Quantity(7.83, 'mile/hour')>

# Perform calculations
pace = (1 / speed).to("minute/kilometer")  # Calculate pace
print(pace)  # <Quantity(4.76, 'minute/kilometer')>
```

## Common Patterns

### Converting Multiple Activities

```python
activities = client.get_activities(limit=10)

for activity in activities:
    distance_mi = uh.miles(activity.distance)
    speed_mph = uh.mph(activity.average_speed)
    elevation_ft = uh.feet(activity.total_elevation_gain)

    print(f"{activity.name}: {distance_mi:.2f} mi @ {speed_mph:.2f} mph")
```

### Calculating Pace

```python
# Strava provides speed, but runners often want pace
activity = client.get_activity(123456789)

# Convert speed (m/s) to pace (min/km or min/mile)
from stravalib.unit_registry import ureg

speed = ureg.Quantity(activity.average_speed, "meter/second")
pace_per_km = (1 / speed).to("minute/kilometer")
pace_per_mile = (1 / speed).to("minute/mile")

print(f"Pace: {pace_per_km:.2f} min/km or {pace_per_mile:.2f} min/mile")
```

### Formatting Output

```python
# Get just the numeric value
distance_mi = uh.miles(activity.distance)
print(f"Distance: {distance_mi.magnitude:.2f} miles")

# Or use the full quantity
print(f"Distance: {distance_mi:.2f}")  # Includes unit
```

## Tips

1. **Strava's Default Units**: Strava API returns:
   - Distance in meters
   - Speed in meters/second
   - Elevation in meters
   - Weight in kilograms
   - Temperature in Celsius

2. **Chaining Conversions**: You can convert between any compatible units:
   ```python
   # Convert meters -> feet -> yards
   distance = uh.meters(5000)
   distance.to("foot").to("yard")
   ```

3. **Unit Arithmetic**: Pint quantities support math operations:
   ```python
   total_distance = uh.miles(5) + uh.kilometers(3)
   print(total_distance.to("mile"))  # Automatically converts
   ```

## See Also

- [Pint Documentation](https://pint.readthedocs.io/)
- [Strava API Documentation](https://developers.strava.com/docs/reference/)
- [stravalib.unit_helper API Reference](../reference/unit_helper.rst)
