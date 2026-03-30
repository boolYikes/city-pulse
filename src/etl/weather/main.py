from etl.weather.ingest import run_weather_job


def handler(event, context):
    lat = event["lat"]
    lon = event["lon"]

    run_weather_job(lat, lon)  # noqa
    return {"statusCode": 200, "body": "ok"}


# For local tests
if __name__ == "__main__":
    # Central Park
    LAT = 40.769804
    LON = -73.974817
    event = {"lat": LAT, "lon": LON}
    res = handler(event, {})
    print(res)
