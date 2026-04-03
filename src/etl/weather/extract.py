"""
The functions parameterizes the location but it's not meant to be fully dynamic,
meaning that cities outside the US must be PoC-ed anew because it is highly probable that the schema is different
"""

from __future__ import annotations
import json
from os.path import join
from os import makedirs
from typing import List, TYPE_CHECKING

from etl.common import DotDict, make_request, to_key_string

if TYPE_CHECKING:
    from etl.config import ETLConfig


def run_weather_job(config: ETLConfig):
    WEATHER_URL = f"https://api.weather.gov/points/{config.lat},{config.lon}"

    weather_res = make_request(WEATHER_URL)
    weather = DotDict(weather_res)

    sunrise = weather.properties.astronomicalData.sunrise
    sunset = weather.properties.astronomicalData.sunset
    city = weather.properties.relativeLocation.properties.city
    state = weather.properties.relativeLocation.properties.state
    tz = weather.properties.timeZone
    forecast_url = weather.properties.forecast

    forecast_res = make_request(forecast_url)
    forecast = DotDict(forecast_res)

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

    # save result
    dt, ts = to_key_string(updated_at)
    filename = f"{ts}.json"

    if config.is_prod:
        from etl.common import put_s3_object

        key = join(config.pipeline, f"city={config.city}", dt, filename)
        put_s3_object(
            config.client,
            config.bucket,
            key=key,
            data=json.dumps(cleaned).encode("utf-8"),
        )
        return key
    else:
        from pathlib import Path

        proj_root = Path(__file__).resolve().parent.parent.parent.parent
        path = join(proj_root, "data", config.pipeline, dt)
        makedirs(path, exist_ok=True)
        with open(join(path, filename), "w") as f:
            json.dump(cleaned, f)
        return join(path, filename)
