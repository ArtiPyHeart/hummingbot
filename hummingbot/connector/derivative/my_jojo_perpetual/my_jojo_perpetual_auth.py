import binascii
from typing import Any, Dict
from urllib.parse import urlencode

import web3

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_utils import current_time_millis
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class MyJojoPerpetualAuth(AuthBase):
    def __init__(self, public_key: str, secret_key: str):
        self._public_key = public_key
        self._secret_key = secret_key

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        if not request.params:
            request.params = {}
        request.params["timestamp"] = current_time_millis()
        request.params["account"] = self._public_key
        request.params["signature"] = self.sign_message(request.params)
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        # 需要在url中直接添加params
        return request

    def sign_message(self, raw_message: Dict[str, Any]) -> str:
        raw_message = dict(sorted(raw_message.items()))
        url_params = urlencode(raw_message)
        message = "\x19Ethereum Signed Message:\n{}{}".format(len(url_params), url_params)
        message_hash = web3.Web3.keccak(text=message)
        signed_message = web3.Account.signHash(message_hash, private_key=self._secret_key)
        signature = signed_message.signature
        if signature[64] == 1:
            signature[64] = 28
        elif signature[64] == 0:
            signature[64] = 27
        final_signature = f"0x{binascii.hexlify(signature).decode()}"
        return final_signature
