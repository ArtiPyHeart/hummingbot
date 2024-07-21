import binascii
from pprint import pprint
from urllib.parse import urlencode, urljoin

import requests
import web3

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    ACCOUNT_URL,
    PERPETUAL_BASE_URL,
)
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_utils import current_time_millis


def sign_message(secret_key, **kwargs):
    raw = dict(kwargs)
    raw_message = dict(sorted(raw.items()))
    url_params = urlencode(raw_message)
    message = f"\x19Ethereum Signed Message:\n{len(url_params)}{url_params}"
    message_hash = web3.Web3.keccak(text=message)
    signed_message = web3.Account.signHash(message_hash, private_key=secret_key)
    signature = signed_message.signature
    print(signature)
    if signature[64] == 1:
        signature[64] = 28
    elif signature[64] == 0:
        signature[64] = 27
    final_signature = f"0x{binascii.hexlify(signature).decode()}"
    return final_signature


PUBLIC_KEY = ""
PRIVATE_KEY = ""

if __name__ == "__main__":
    url = urljoin(PERPETUAL_BASE_URL, ACCOUNT_URL)
    account = PUBLIC_KEY
    timestamp = current_time_millis()
    params = {
        "account": account,
        "timestamp": current_time_millis(),
    }
    sign = sign_message(PRIVATE_KEY, **params)
    print(sign)
    params["signature"] = sign
    response = requests.get(url, params=params)
    print(response.status_code)
    pprint(response.json())
