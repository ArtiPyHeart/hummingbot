import binascii
import time
from urllib.parse import urlencode
from typing import Dict, Any
from web3.auto import w3

from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


def current_time_millis() -> int:
    return time.perf_counter_ns() // 1000000


class MyJojoPerpetualAuth(AuthBase):
    def __init__(self, public_key: str, secret_key: str):
        self._public_key = public_key
        self._secret_key = secret_key

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        request.is_auth_required = True
        if request.params is None:
            request.params = {}
        request.params["timestamp"] = current_time_millis()
        request.params["signature"] = self.sign_message(request.params)
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        request.is_auth_required = True
        if not hasattr(request, "payload"):
            request.payload = {}
        request.payload["timestamp"] = current_time_millis()
        request.payload["signature"] = self.sign_message(request.payload)
        return request

    def sign_message(self, raw_message: Dict[str, Any]) -> str:
        raw_message = dict(sorted(raw_message.items()))
        url_params = urlencode(raw_message)
        message = "\x19Ethereum Signed Message:\n{}{}".format(len(url_params), url_params)
        message_hash = w3.keccak(text=message)
        signed_message = w3.eth.account.signHash(message_hash, private_key=self._secret_key)
        signature = signed_message.signature
        if signature[64] == 1:
            signature[64] = 28
        elif signature[64] == 0:
            signature[64] = 27
        final_signature = f"0x{binascii.hexlify(signature).decode()}"
        return final_signature
