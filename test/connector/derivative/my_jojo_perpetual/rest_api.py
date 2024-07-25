from pprint import pprint
from urllib.parse import urljoin

import requests

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    ACCOUNT_URL,
    PERPETUAL_BASE_URL,
)
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_utils import current_time_millis
from hummingbot.connector.time_synchronizer import TimeSynchronizer

PUBLIC_KEY = ""
PRIVATE_KEY = ""

time_sync = TimeSynchronizer()
auth = MyJojoPerpetualAuth(PUBLIC_KEY, PRIVATE_KEY, time_sync)

if __name__ == "__main__":
    url = urljoin(PERPETUAL_BASE_URL, ACCOUNT_URL)
    account = PUBLIC_KEY
    timestamp = current_time_millis()
    params = {
        "account": account,
        "timestamp": current_time_millis(),
    }
    sign = auth.sign_message(**params)
    print(sign)
    params["signature"] = sign
    response = requests.get(url, params=params)
    print(response.status_code)
    pprint(response.json())
