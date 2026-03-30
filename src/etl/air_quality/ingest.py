# use radius quary: ?coordinates=35.14942,136.90610&radius=12000


def run_openaq_ingestion(lat: float, lon: float, rad: int = 12000):
    # radius is in meters
    url = f"https://api.openaq.org/v3/locations?coordinates={lat},{lon}&radius={rad}"
    print(url)
    # 1. extract sensor ids and then query sensor measurement
    # tz: results[].timezone
    # name: results[].name -> this returns name in native language. better use the result from the weather api
    # sensors: results[].sensors[].id
    # sensor measure name: results[].sensors[].parameter.name
    # sensor measure unit: results[].sensors[].parameter.units
    # sensor measure dp name: results[].sensors[].parameter.displayName

    # 2. get measurement
    # /v3/sensors/{sensors_id}/measurements
    # use limit!!!
    # example : https://api.openaq.org/v3/sensors/6516828/measurements?limit=10
    # name: results[].parameter.name
    # units: results[].parameter.units
    # val: results[].value

    pass
