from etl.weather.extract import run_weather_job
from etl.config import init


def extract_handler(event, context):
    config = init()
    run_weather_job(config)
    return {"statusCode": 200, "body": "ok"}


# For local dev
if __name__ == "__main__":
    from etl.config import ETLConfig

    # Central Parks
    LAT = 40.769804
    LON = -73.974817
    CITY = "NewYork"
    event = {"lat": LAT, "lon": LON}
    config = ETLConfig(
        log_level="DEBUG",
        city=CITY,
        lat=LAT,
        lon=LON,
        ts="",  # This is not used at all
        rad=0,  # Not used in this pipeline
        bucket="",  # Not for local
        pipeline="bronze",
        openaq_api_key="",  # Not for this pipeline
        is_prod=False,
        client=None,
        s3_config={},  # Not for local
    )
    run_weather_job(config)
