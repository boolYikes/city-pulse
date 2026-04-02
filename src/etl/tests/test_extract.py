from etl.weather.extract import run_weather_job
from etl.common import get_s3_object


def test_run_weather_job(config):
    key = run_weather_job(config)
    data = get_s3_object(config.client, config.bucket, key)
    assert data is not None
