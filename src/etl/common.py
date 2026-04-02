from pathlib import Path
from datetime import datetime, timezone
import os


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
def check_file_exists(path: str, base_name: str) -> bool:
    return (Path(path) / f"{base_name}.json").exists()


def get_s3_client(s3_config):
    import boto3

    return boto3.client("s3", **s3_config)


def get_s3_object(client, bucket: str, key: str):
    from botocore.exceptions import ClientError

    try:
        response = client.get_object(Bucket=bucket, Key=key)
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


def get_environment():
    truthy = {"1", "true", "t", "yes", "y"}
    falsy = {"0", "false", "f", "no", "n"}

    env = os.environ.get("environment")
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
