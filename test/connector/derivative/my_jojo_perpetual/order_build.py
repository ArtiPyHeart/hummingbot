import time
from decimal import Decimal
from pprint import pprint
from test.connector.derivative.my_jojo_perpetual.rest_api import PRIVATE_KEY, PUBLIC_KEY
from urllib.parse import urljoin

import requests

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    ORDER_BUILD_URL,
    ORDER_URL,
    PERPETUAL_BASE_URL,
    TimeInForce,
)
from hummingbot.connector.time_synchronizer import TimeSynchronizer

time_sync = TimeSynchronizer()
auth = MyJojoPerpetualAuth(PUBLIC_KEY, PRIVATE_KEY, time_sync)

if __name__ == "__main__":
    url = urljoin(PERPETUAL_BASE_URL, ORDER_BUILD_URL)
    current_time = int(time_sync.time() * 1000)
    params = {
        "marketId": "ethusdc",
        "side": "BUY",
        "orderType": "LIMIT",
        "amount": Decimal("0.02"),
        "price": Decimal("2000"),
        "timeInForce": TimeInForce.GTC.value,
        "account": PUBLIC_KEY,
        "timestamp": current_time,
    }
    params["signature"] = auth.sign_message(**params)
    response = requests.post(url, data=params)
    print(response.status_code)
    build_info = response.json()
    pprint(build_info)

    order_url = urljoin(PERPETUAL_BASE_URL, ORDER_URL)
    request_params = {
        "marketId": "ethusdc",
        "side": "BUY",
        "orderType": "LIMIT",
        "amount": Decimal("0.02"),
        "price": Decimal("2000"),
        "timeInForce": TimeInForce.GTC.value,
        "orderSignature": auth.sign_order(build_info["orderHash"]),
        "info": build_info["order"]["info"],
        "gasFeeQuotation": build_info["gasFeeQuotation"],
        "account": PUBLIC_KEY,
        "timestamp": current_time,
    }
    request_params["signature"] = auth.sign_message(**request_params)
    response = requests.post(order_url, data=request_params)
    print(response.status_code)
    order_info = response.json()
    pprint(order_info)

    time.sleep(61)
    cancel_url = urljoin(PERPETUAL_BASE_URL, ORDER_URL)
    cancel_params = {
        "orderId": order_info["id"],
        "marketId": "ethusdc",
    }
    cancel_params["signature"] = auth.sign_message(**cancel_params)
    response = requests.delete(cancel_url, data=cancel_params)
    print(response.status_code)
    cancel_info = response.json()
    pprint(cancel_info)
