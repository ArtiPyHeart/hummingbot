from pprint import pprint
from urllib.parse import urljoin

import requests

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS

if __name__ == "__main__":
    url = urljoin(CONSTANTS.PERPETUAL_BASE_URL, CONSTANTS.EXCHANGE_INFO_URL)
    resp = requests.get(url)
    print(resp.status_code)
    pprint(resp.json())
