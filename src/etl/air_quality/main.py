from etl.air_quality.ingest import run_openaq_ingestion


def handler(event, context):
    lat = event["lat"]
    lon = event["lon"]
    city = event["city"]
    rad = event.get("rad", 12000)
    ts = event.get("ts", None)
    run_openaq_ingestion(city, lat, lon, rad, ts)


# for dev
if __name__ == "__main__":
    # Central Park
    LAT = 40.769804
    LON = -73.974817
    event = {"lat": LAT, "lon": LON, "city": "New York", "rad": 12000, "ts": None}

    handler(event, {})
