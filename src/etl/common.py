from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from etl.config import ETLConfig


# for dot operator enabling
class DotDict(dict):
    def __getattr__(self, key):
        val = self[key]
        if isinstance(val, dict):
            return DotDict(val)
        if isinstance(val, list):
            return [DotDict(v) if isinstance(v, dict) else v for v in val]
        return val


def make_request(url: str, api_key: str = ""):
    import requests

    headers = {
        "User-Agent": "CityPulse/0.1 ()",
        "X-API-Key": api_key,
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()


# for local only
def check_file_exists(path: str, config: ETLConfig) -> bool:
    """
    Checks if file exists in s3 or locally based on environment
    """
    if config.is_prod:
        try:
            obj = get_s3_object(config.client, bucket=config.bucket, key=path)
        except Exception as e:
            config.logger.debug(e)  # need to convert plain error to a meaningful one
        return obj is not None
    return Path(path).exists()


def write_file(path: str, data: bytes, config: ETLConfig):
    """
    Path in key-like format
    """
    if config.is_prod:
        put_s3_object(config.client, bucket=config.bucket, key=path, data=data)
    else:
        with open(path, "wb") as f:
            f.write(data)


def read_file(path: str, config: ETLConfig) -> bytes:
    """
    Path in key-like format
    """
    if config.is_prod:
        obj = get_s3_object(config.client, bucket=config.bucket, key=path)
        if obj is None:
            raise FileNotFoundError(f"File {path} not found in bucket {config.bucket}")
        return obj
    else:
        with open(path, "rb") as f:
            return f.read()


def get_s3_client(s3_config):
    import boto3

    return boto3.client("s3", **s3_config)


def get_s3_object(client, bucket: str, key: str):
    from botocore.exceptions import ClientError

    try:
        response = client.get_object(Bucket=bucket, Key=key)
        # json.loads() assumes utf-8 later so .decode() is omitted
        return response["Body"].read()
    except ClientError as e:
        print(f"Error fetching object {key} from bucket {bucket}: {e}")
        return None


def put_s3_object(client, bucket: str, key: str, data: bytes):
    from botocore.exceptions import ClientError

    try:
        client.put_object(Bucket=bucket, Key=key, Body=data)
        print(f"Successfully uploaded {key} to bucket {bucket}")
    except ClientError as e:
        print(f"Error uploading object {key} to bucket {bucket}: {e}")


def is_prod():
    truthy = {"1", "true", "t", "yes", "y"}
    falsy = {"0", "false", "f", "no", "n"}

    env = os.environ.get("IS_PROD")
    IS_TEST = env.strip().lower()

    if IS_TEST in truthy:
        return True
    elif IS_TEST in falsy:
        return False
    else:
        raise Exception(f"Invalid value {env} for environment variable 'environment'")


def to_zulu_format(dt_string: str):
    """
    Converts a datetime string to zulu style format
    """
    dt = datetime.fromisoformat(dt_string)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_key_string(dt_string: str):
    """
    Converts a datetime string to an object storage key style string
    Also returns h-m-s
    """
    dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
    converted = dt.strftime("year=%Y/month=%m/day=%d %H-%M-%S")
    return converted.split()


def is_valid_event(event: dict) -> bool:
    required_keys = {"log_level", "city", "lat", "lon", "ts", "rad", "BUCKET"}
    if not required_keys.issubset(event.keys()):
        return False

    # type validation
    if not isinstance(event["log_level"], str):
        return False
    if not isinstance(event["city"], str):
        return False
    if not isinstance(event["lat"], (int, float)):
        return False
    if not isinstance(event["lon"], (int, float)):
        return False
    if event["ts"] is not None and not isinstance(event["ts"], str):
        return False
    if not isinstance(event["rad"], int):
        return False
    if not isinstance(event["BUCKET"], str):
        return False

    return True
