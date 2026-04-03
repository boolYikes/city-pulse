from etl.air_quality.extract import run_openaq_ingestion
from etl.config import init


def extract_handler(event, context):
    """
    log_level, city, lat, lon, ts, rad, bucket must be passed in event.
    """
    # load config
    config = init(event)
    run_openaq_ingestion(config)
    return {"statusCode": 200, "body": "ok"}


# for local dev
if __name__ == "__main__":
    # Central Park
    LAT = 40.769804
    LON = -73.974817
    event = {"lat": LAT, "lon": LON, "city": "New York", "rad": 12000, "ts": None}
    from etl.config import ETLConfig
    from os import environ

    CITY = "NewYork"
    event = {"lat": LAT, "lon": LON}
    config = ETLConfig(
        log_level="DEBUG",
        city=CITY,
        lat=LAT,
        lon=LON,
        ts="2026-04-03T14:27:00Z",
        rad=12000,
        bucket="",
        pipeline="bronze",
        openaq_api_key=environ["OPENAQ_API_KEY"],
        is_prod=False,
        client=None,
        s3_config={},
    )
    run_openaq_ingestion(config)
