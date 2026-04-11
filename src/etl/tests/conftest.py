import boto3
import pytest

from etl.config import ETLConfig

BUCKET_NAME = "test-bucket"


@pytest.fixture(scope="session")
def config():
    """
    This helps skip the init() of the config
    Config determines the S3 client
    """
    import os

    LAT = 40.769804
    LON = -73.974817
    CITY = "test-new-york"
    config = ETLConfig(
        log_level="DEBUG",
        city=CITY,
        lat=LAT,
        lon=LON,
        ts="2026-04-03T14:27:00Z",
        rad=12000,
        bucket=BUCKET_NAME,
        pipeline="test-bronze",
        openaq_api_key=os.getenv("OPENAQ_API_KEY"),  # error on missing key
        is_prod=True,  # This is for testing S3 client, not for local file system
        client=None,
        s3_config={
            "endpoint_url": "http://localhost:9000",
            "aws_access_key_id": "minio_test",
            "aws_secret_access_key": "minio_test",
            "region_name": "us-east-1",
        },
    )

    config.client = boto3.client(
        "s3",
        endpoint_url=config.s3_config["endpoint_url"],
        aws_access_key_id=config.s3_config["aws_access_key_id"],
        aws_secret_access_key=config.s3_config["aws_secret_access_key"],
        region_name=config.s3_config["region_name"],
    )

    return config


@pytest.fixture(scope="session", autouse=True)
def bucket_provider(config):
    config.client.create_bucket(Bucket=BUCKET_NAME)
    # both on local and workflow, below is done automatically so commenting out for now
    # yield
    # s3 = boto3.resource(
    #     "s3",
    #     endpoint_url=config.s3_config["endpoint_url"],
    #     aws_access_key_id=config.s3_config["aws_access_key_id"],
    #     aws_secret_access_key=config.s3_config["aws_secret_access_key"],
    #     region_name=config.s3_config["region_name"],
    # )
    # b = s3.Bucket(BUCKET_NAME)
    # b.objects.all().delete()
    # config.client.delete_bucket(Bucket=BUCKET_NAME)
