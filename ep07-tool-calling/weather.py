"""
The real tool — Episode 7
=========================
This is plain, boring code. No AI in it.

`get_weather(city)` takes a city name, looks up its coordinates, and returns
the current conditions. The model will NEVER run this function directly. It
will only ask us (via a structured tool-call request) to run it, and our code
does the actual work.

Notice what this function does NOT take: a date. Its only argument is `city`,
and it returns the weather happening RIGHT NOW. That's the tool's contract.
It's exactly why "what should I pack for next week?" can't be answered here —
the tool has no way to look into the future, and no date parameter to try. Not
a bug. Just the limit of this particular tool.

We use Open-Meteo because it needs no API key, so nothing sensitive shows on
camera and the demo is reproducible. Two free endpoints:
  1. Geocoding  — turn a city name into latitude/longitude.
  2. Forecast   — get current weather at those coordinates.

Only the Python standard library is used here (urllib), so there is no extra
dependency to install for the HTTP calls.
"""

import json
import urllib.parse
import urllib.request

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → plain English.
# https://open-meteo.com/en/docs  (subset, enough for the demo)
WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
}


def _get_json(url: str, params: dict) -> dict:
    """GET a URL with query params and parse the JSON response."""
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get_weather(city: str) -> dict:
    """
    Return the current weather for `city`.

    On success:
      {"city": "Toronto", "country": "Canada", "temperature_c": 12.3,
       "conditions": "light rain", "wind_kph": 14.0}

    On failure (city not found, network error, etc.):
      {"error": "City 'the Paris office next week' not found."}

    Returning a plain error dict (instead of raising) matters: it lets the
    caller hand the error straight back to the model, which can then retry
    with a better argument. That recovery loop is the whole point of the fix.
    """
    try:
        # ── Step A: geocode the city name into coordinates ──
        geo = _get_json(GEOCODE_URL, {"name": city, "count": 1, "language": "en", "format": "json"})
        results = geo.get("results")
        if not results:
            return {"error": f"City '{city}' not found."}

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]

        # ── Step B: fetch current conditions at those coordinates ──
        forecast = _get_json(
            FORECAST_URL,
            {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
            },
        )
        current = forecast["current"]
        code = current.get("weather_code")

        return {
            "city": place.get("name", city),
            "country": place.get("country", ""),
            "temperature_c": current.get("temperature_2m"),
            "conditions": WEATHER_CODES.get(code, f"weather code {code}"),
            "wind_kph": current.get("wind_speed_10m"),
        }

    except Exception as exc:  # noqa: BLE001 — demo: surface any failure as data
        return {"error": f"Weather lookup failed for '{city}': {exc}"}


# Run this file directly to confirm the tool works BEFORE the shoot.
#   python3 weather.py
if __name__ == "__main__":
    for test_city in ["Toronto", "Paris", "Tokyo"]:
        print(f"get_weather({test_city!r}) ->")
        print(f"  {get_weather(test_city)}\n")
