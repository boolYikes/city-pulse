class ETLConfig:
    """
    One config per one ETL process.
    """

    def __init__(
        self,
        log_level: str,
        # used in api queries
        city: str,
        lat: float,
        lon: float,
        ts: str,
        rad: int,
        # used in key and path
        bucket: str,
        pipeline: str,
        openaq_api_key: str,
        is_prod: bool,
        # defaults to None on test environment
        client=None,
        s3_config: dict = None,
    ):
        self.log_level = log_level
        self.city = city
        self.lat = lat
        self.lon = lon
        self.ts = ts
        self.rad = rad
        self.bucket = bucket
        self.pipeline = pipeline
        self.openaq_api_key = openaq_api_key
        self.is_prod = is_prod
        self.client = client
        self.s3_config = s3_config or {}


def init():
    """
    Dotenv was not used to minimize footprint and security
    So on local setup, you need to run it from a script.
    """
    import os

    from etl.common import get_environment, get_s3_client

    is_prod = get_environment()

    config = ETLConfig(
        log_level=os.environ.get("LOG_LEVEL"),
        city=os.environ.get("CITY"),
        lat=os.environ.get("LAT"),
        lon=os.environ.get("LON"),
        ts=os.environ.get("TS"),
        rad=os.environ.get("RAD"),
        bucket=os.environ.get("BUCKET"),
        pipeline=os.environ.get("PIPELINE"),
        openaq_api_key=os.environ.get("OPENAQ_API_KEY"),
        s3_config={
            "endpoint_url": os.environ.get("S3_ENDPOINT_URL"),
            "aws_access_key_id": os.environ.get("S3_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.environ.get("S3_SECRET_ACCESS_KEY"),
            "region_name": os.environ.get("S3_REGION_NAME"),
        },
        is_prod=is_prod,
    )

    if is_prod:
        config.client = get_s3_client(config.s3_config)

    return config
