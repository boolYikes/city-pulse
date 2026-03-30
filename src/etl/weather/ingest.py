"""
The functions parameterizes the location but it's not meant to be fully dynamic,
meaning that cities outside the US must be PoC-ed anew because it is highly probable that the schema is different
"""

from __future__ import annotations
import json
from typing import List

import requests

from etl.common import DotDict
from etl.common import Config


def run_weather_job(lat: float, lon: float, dev=True):
    WEATHER_URL = f"https://api.weather.gov/points/{lat},{lon}"
    HEADERS = {"User-Agent": "CityPulsePoC/0.1 (Ad Hoc)"}

    weather_res = requests.get(WEATHER_URL, headers=HEADERS)
    weather_res.raise_for_status()
    weather = DotDict(weather_res.json())

    sunrise = weather.properties.astronomicalData.sunrise
    sunset = weather.properties.astronomicalData.sunset
    city = weather.properties.relativeLocation.properties.city
    state = weather.properties.relativeLocation.properties.state
    tz = weather.properties.timeZone
    forecast_url = weather.properties.forecast

    forecast_res = requests.get(forecast_url, headers=HEADERS)
    forecast_res.raise_for_status()
    forecast = DotDict(forecast_res.json())

    updated_at = forecast.properties.updateTime
    periods: List = forecast.properties.periods

    cleaned = {
        "city": city,
        "state": state,
        "timezone": tz,
        "sunrise": sunrise,
        "sunset": sunset,
        "updated_at": updated_at,
        "forecast": periods,
    }

    config = Config()
    # config should include connections?
    # config should include file name conventions
    curr_dir = config.dev_storage_path if dev else config.prod_storage_path
    # temporary.
    with open(curr_dir / "example.json", "w") as f:
        json.dump(cleaned, f)
