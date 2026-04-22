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
        ts: str,  # used in openaq api query. passed from eventbridge event
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
        """
        ts example: 2026-04-03T14:27:00Z
        """
        import logging

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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))


def init(event: dict) -> ETLConfig:
    """
    Dotenv was not used to minimize footprint and for security
    So on local setup, you need to run it from a script.
    """
    import os

    from etl.common import is_prod, get_s3_client, is_valid_event

    if not is_valid_event(event):
        raise ValueError(
            "Invalid event. Required keys: log_level, city, lat, lon, ts(optional), rad(optional), bucket"
        )

    config = ETLConfig(
        log_level=event["log_level"],
        city=event["city"],
        lat=event["lat"],
        lon=event["lon"],
        ts=event.get("ts", None),
        rad=event.get("rad", 12000),
        bucket=event["BUCKET"],
        # These need environment variables
        pipeline=os.environ.get("PIPELINE"),
        openaq_api_key=os.environ.get("OPENAQ_API_KEY", None),
        s3_config={
            "endpoint_url": os.environ.get("S3_ENDPOINT_URL"),
            "aws_access_key_id": os.environ.get("S3_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.environ.get("S3_SECRET_ACCESS_KEY"),
            "region_name": os.environ.get("S3_REGION_NAME"),
        },
        is_prod=is_prod(),
    )

    if config.is_prod:
        config.client = get_s3_client(config.s3_config)

    return config
