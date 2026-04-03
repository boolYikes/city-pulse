import time
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from etl.config import ETLConfig

from etl.common import (
    DotDict,
    make_request,
    check_file_exists,
    write_file,
    read_file,
    to_key_string,
)
from datetime import datetime, timezone, timedelta


def run_openaq_ingestion(config: ETLConfig) -> list[str]:
    """
    ts: ISO 8601 format, e.g. 2023-01-31T23:59:59Z / passed by Step Functions
    Returns path to the file in s3 or local
    """

    # Use cache first for the meta data since it doesn't change often.
    path = f"{config.pipeline}/city={config.city}/meta_openaq.json"
    if not check_file_exists(path, config):
        # radius is in meters
        OPENAQ_URL = f"https://api.openaq.org/v3/locations?coordinates={config.lat},{config.lon}&radius={config.rad}"

        openaq_res = make_request(OPENAQ_URL)
        aqs = DotDict(openaq_res).results

        # 1. extract sensor ids and then query sensor measurement
        # timezone = aq.results[].timezone
        # name: results[].name -> this returns name in native language. better use the result from the weather api
        # sensors: results[].sensors[].id
        # sensor measure name: results[].sensors[].parameter.name
        # sensor measure unit: results[].sensors[].parameter.units
        # sensor measure dp name: results[].sensors[].parameter.displayName
        aqs_transformed = list(
            map(
                lambda aq: {
                    "timezone": aq.timezone,
                    "name": aq.name,
                    "sensors": list(
                        map(
                            lambda sensor: {
                                "id": sensor.id,
                                "measure_name": sensor.parameter.name,
                                "measure_unit": sensor.parameter.units,
                                "measure_dp_name": sensor.parameter.displayName,
                            },
                            aq.sensors,
                        )
                    ),
                },
                aqs,
            )
        )
        write_file(path, json.dumps(aqs_transformed).encode("utf-8"), config)
    else:
        aqs_transformed = json.loads(read_file(path, config))

    # 2. get measurement
    # https://api.openaq.org/v3/sensors/{sensors_id}/measurements/hourly?datetime_from=2023-01-01T00:00:00Z&datetime_to=2023-01-31T23:59:59Z
    # datetimeTo is optional.
    # number of found measurements: results[].meta.found
    sensors_done = (
        set()
    )  # sensors are unique so a top-level record will do to track dupes

    # I think I should just use one location.
    # Sensors sometimes overlap across locations
    # and around 12k radius it probably wouldn't be meaningful
    # for aq in aqs_transformed:
    aq = aqs_transformed[0]
    results = []
    for sensor in aq["sensors"]:
        sensor_id = sensor["id"]

        # don't make dupe queries!
        if sensor_id in sensors_done:
            continue
        sensors_done.add(sensor_id)

        # floor the time to nearest hour
        if config.ts is None:
            # just in case ts was not passed
            now = (
                datetime.now(timezone.utc)
                .replace(minute=0, second=0, microsecond=0)
                .strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        else:
            dt = datetime.strptime(config.ts, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            dt = dt.replace(minute=0, second=0, microsecond=0)
            now = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        found = False
        while not found:
            # check cache
            # local only. use time-based partition key. e.g., 2026/03/31
            key_style_dt, ts = to_key_string(now)
            filename = f"{sensor_id}_{ts}.json"
            key = f"{config.pipeline}/city={config.city}/{key_style_dt}/{filename}"
            if check_file_exists(key, config):
                found = True
                continue

            OPENAQ_MEASUREMENT_URL = f"https://api.openaq.org/v3/sensors/{sensor_id}/measurements/hourly?datetime_from={now}"
            measurement_res = make_request(OPENAQ_MEASUREMENT_URL)
            # if not found, go back in time until there is result
            if measurement_res["meta"]["found"] == 0:
                dt = datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ").replace(
                    tzinfo=timezone.utc
                )
                dt = dt - timedelta(hours=1)
                now = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                found = True

            time.sleep(1)

        measurements = DotDict(measurement_res).results
        # period: results[].period.{datetimeFrom,datetimeTo}.{local,utc}
        # interval: results[].period.interval
        # units: results[].parameter.units
        # name: results[].parameter.name
        # summary: results[].summary
        # value: results[].value
        payload = list(
            map(
                lambda m: {
                    "dp_name": sensor.get("measure_dp_name", sensor["measure_name"]),
                    "name": m.parameter.name,
                    "units": m.parameter.units,
                    "value": m.value,
                    "interval": m.period.interval,
                    "start": {
                        "local": m.period.datetimeFrom.local,
                        "utc": m.period.datetimeFrom.utc,
                    },
                    "end": {
                        "local": m.period.datetimeTo.local,
                        "utc": m.period.datetimeTo.utc,
                    },
                    "summary": m.summary,
                },
                measurements,
            )
        )

        # 3. save to s3
        write_file(key, json.dumps(payload).encode("utf-8"), config)
        results.append(key)
    return results
