from dataclasses import dataclass
from pathlib import Path
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


@dataclass(frozen=True)
class Config:
    dev_storage_path = Path(__file__).parent.parent.parent / "data"
    # add s3 path as
    prod_storage_path = ""
    openaq_api_key = os.environ["OPENAQ_API_KEY"]  # error on missing key


def make_request(url: str, headers: dict = None):
    import requests

    if headers is None:
        headers = {
            "User-Agent": "CityPulsePoC/0.1 (Ad Hoc)",
            "X-API-Key": Config.openaq_api_key,
        }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()


# for local only
def check_file_exists(path: str, base_name: str) -> bool:
    return (Path(path) / f"{base_name}.json").exists()
