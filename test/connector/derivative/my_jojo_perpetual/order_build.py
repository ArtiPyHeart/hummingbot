from urllib.parse import urljoin

import requests
from pprint import pprint

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    ORDER_BUILD_URL,
    PERPETUAL_BASE_URL,
    TimeInForce,
)
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_utils import (
    current_time_millis,
    get_expiry_timestamp_in_millis,
)
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from test.connector.derivative.my_jojo_perpetual.rest_api import PUBLIC_KEY, PRIVATE_KEY

auth = MyJojoPerpetualAuth(PUBLIC_KEY, PRIVATE_KEY)
time_sync = TimeSynchronizer()

if __name__ == "__main__":
    url = urljoin(PERPETUAL_BASE_URL, ORDER_BUILD_URL)
    current_time = int(time_sync.time() * 1000)
    params = {
        "marketId": "ethusdc",
        "side": "BUY",
        "orderType": "LIMIT",
        "amount": "0.02",
        "price": "2000",
        "timeInForce": TimeInForce.GTT.value,
        "expiration": current_time + 60_1000,  # 结束时间，毫秒时间戳
        "account": PUBLIC_KEY,
        "timestamp": current_time,
    }
    params["signature"] = auth.sign_message(**params)
    response = requests.post(url, data=params)
    print(response.status_code)
    pprint(response.json())
