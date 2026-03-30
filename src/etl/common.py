from dataclasses import dataclass
from pathlib import Path


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
