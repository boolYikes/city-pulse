"""
Clean raw data processed by extract.py,
and run aggregation every day at 00:00 UTC to build analytics tables.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import json
from os import environ
from datetime import datetime, timezone

from pandas import json_normalize

from etl.common import read_file, to_key_string

if TYPE_CHECKING:
    from etl.config import ETLConfig


def run_openaq_transform(keys: list[str], config: ETLConfig):
    # load up all the aq jsons within the timeframe
    data = [json.loads(read_file(key, config)) for key in keys]

    # each dataset should contain 1 row
    if any(map(lambda p: len(p) != 1, data)):
        raise Exception(f"Number of rows among datasets do not match!: {data}")

    # parse facts
    # Don't keep fact wide.
    # City name and date are already in keys but for readability, I keep them
    parsed_fact = list(
        map(
            lambda p: {
                "city": config.city,
                "date": p[0]["end"]["utc"],
                "pollutant": p[0]["name"],
                "value": p[0]["value"],
            },
            data,
        )
    )

    # parse dims
    # dims are snapshotted alongside facts every update -> simplicity vs storage tradeoff
    # if I avoid duplicate dims -> query must resolve latest dim snapshot where dim_date <= fact_date -> storage vs compute tradeoff
    # if i wanted to do SCD 2 + parquet + lakehouse -> only infer from `valid_from` + id
    parsed_dims = list(
        map(
            lambda p: {
                "name": p[0]["name"],
                "display_name": p[0]["dp_name"],
                "interval": p[0]["interval"],
                "units": p[0]["units"],
            },
            data,
        )
    )

    # keys: extract date
    # NOTE: This is boiler plate! See air_quality.extract.py
    if config.ts is None:
        # just in case ts was not passed
        now = (
            datetime.now(timezone.utc)
            .replace(minute=0, second=0, microsecond=0)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    else:
        dt = datetime.strptime(config.ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        dt = dt.replace(minute=0, second=0, microsecond=0)
        now = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    key_style_dt, ts = to_key_string(now)

    fact_filename = f"fact_aq_{now.split('T')[0]}_{ts}.parquet"
    fact_key = f"{config.pipeline}/city={config.city}/{key_style_dt}/{fact_filename}"

    # snapshot - ish ? dim table
    # don't take advantage of columnar design but from small size
    dim_filename = f"dim_aq_pollutants_{now.split('T')[0]}_{ts}.parquet"
    dim_key = f"{config.pipeline}/city={config.city}/{key_style_dt}/{dim_filename}"

    # convert to dataframe,
    fact_df = json_normalize(parsed_fact)
    dims_df = json_normalize(parsed_dims)

    # convert to parquet and save
    fact_df.to_parquet(
        f"s3://{config.bucket}/{fact_key}",
        engine="pyarrow",
        index=False,
        storage_options={
            "key": environ.get("S3_ACCESS_KEY_ID"),
            "secret": environ.get("S3_SECRET_ACCESS_KEY"),
            "client_kwargs": {
                "endpoint_url": environ.get("S3_ENDPOINT_URL"),
                "region_name": environ.get("S3_REGION_NAME"),
            },
        },
    )

    dims_df.to_parquet(
        f"s3://{config.bucket}/{dim_key}",
        engine="pyarrow",
        index=False,
        storage_options={
            "key": environ.get("S3_ACCESS_KEY_ID"),
            "secret": environ.get("S3_SECRET_ACCESS_KEY"),
            "client_kwargs": {
                "endpoint_url": environ.get("S3_ENDPOINT_URL"),
                "region_name": environ.get("S3_REGION_NAME"),
            },
        },
    )

    return fact_key, dim_key


# Intentionally put analytics aggregation in transformation step for semantic clarity,
# but it can be completely detached from the ETL pipeline and run on its own schedule.
def run_openaq_city_grain_analytics(config: ETLConfig):
    """
    Runs city-grain aggregation
    """
    from pyarrow.dataset import dataset
    from pyarrow.fs import S3FileSystem
    # load all fact data for the city

    # this is more like an s3 client.
    fs = S3FileSystem(
        access_key=environ.get("S3_ACCESS_KEY_ID"),
        secret_key=environ.get("S3_SECRET_ACCESS_KEY"),
        endpoint_override=environ.get("S3_ENDPOINT_URL"),
        region=environ.get("S3_REGION_NAME"),
    )

    fact_ds = dataset(  # noqa
        source=f"s3://{config.bucket}/{config.pipeline}/{config.city}",
        format="parquet",
        filesystem=fs,
        partitioning="hive",
        ignore_prefixes=[".", "_", "dim_", "meta_"],
    )

    # Get the latest dim snapshot
    dt = datetime.strptime(config.ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    dt = dt.replace(minute=0, second=0, microsecond=0)
    now = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    key_style_dt, ts = to_key_string(now)

    dim_filename = f"dim_aq_{now.split('T')[0]}_{ts}.parquet"
    dim_key = f"{config.pipeline}/city={config.city}/{key_style_dt}/{dim_filename}"

    dim_ds = dataset(  # noqa
        source=dim_key,
        format="parquet",
        filesystem=fs,
        partitioning="hive",
        ignore_prefixes=[".", "_", "fact_", "meta_"],
    )
    # NOTE: since I snapshot dims alongside facts,
    # we don't have to worry about point in time correctness

    return "temp_key1", "temp_key2"
