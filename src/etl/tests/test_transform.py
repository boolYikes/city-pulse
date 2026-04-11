from etl.air_quality.transform import run_openaq_transform  # noqa
from etl.common import get_s3_object  # noqa


# TODO: write a new fixture just for the silver layer
# fixture should provide keys of both pollutants
def test_run_openaq_transformation(config):
    pass
    # keys = run_openaq_transform(config)
    # for key in keys:
    #     data = get_s3_object(config.client, config.bucket, key)
    #     assert data is not None
