from etl.weather.extract import run_weather_job
from etl.air_quality.extract import run_openaq_ingestion
from etl.common import get_s3_object

# are these integration tests or unit tests? 🤔


def test_run_weather_job(config):
    key = run_weather_job(config)
    data = get_s3_object(config.client, config.bucket, key)
    assert data is not None


def test_run_openaq_ingestion(config):
    keys = run_openaq_ingestion(config)
    for key in keys:
        data = get_s3_object(config.client, config.bucket, key)
        assert data is not None
