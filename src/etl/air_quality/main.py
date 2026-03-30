from etl.air_quality.ingest import run_openaq_ingestion


def handler(event, context):
    lat = event["lat"]
    lon = event["lon"]
    run_openaq_ingestion(lat, lon)


# for dev
if __name__ == "__main__":
    from etl.common import Config

    # Central Park
    LAT = 40.769804
    LON = -73.974817
    event = {"lat": LAT, "lon": LON}
    config = Config()

    handler(event, {})
