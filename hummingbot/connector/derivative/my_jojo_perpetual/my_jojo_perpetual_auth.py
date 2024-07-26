from urllib.parse import urlencode

import web3

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTRequest, WSRequest


class MyJojoPerpetualAuth(AuthBase):
    def __init__(self, public_key: str, secret_key: str, time_sync: TimeSynchronizer):
        self._public_key = public_key
        self._account = web3.Account.from_key(secret_key)
        self._time_sync = time_sync

    @property
    def public_key(self) -> str:
        return self._public_key

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        if not request.params:
            request.params = {}
        order_hash: str = request.params.pop("orderHash")
        if order_hash:
            request.params["orderSignature"] = self.sign_order(order_hash)
        request.params["timestamp"] = int(self._time_sync.time() * 1000)
        request.params["account"] = self._public_key
        request.params["signature"] = self.sign_message(**request.params)
        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        # 需要在url中直接添加params
        return request

    def _sign(self, message) -> str:
        signed_message = self._account.signHash(message)
        signature = signed_message.signature
        if signature[64] == 1:
            signature[64] = 28
        elif signature[64] == 0:
            signature[64] = 27
        final_signature = web3.Web3.to_hex(signature)
        return final_signature

    def sign_message(self, **kwargs) -> str:
        raw_message = dict(sorted(kwargs.items()))
        url_params = urlencode(raw_message)
        message = "\x19Ethereum Signed Message:\n{}{}".format(len(url_params), url_params)
        message_hash = web3.Web3.keccak(text=message)
        return self._sign(message_hash)

    def sign_order(self, order_hash: str):
        order_bytes = web3.Web3.to_bytes(hexstr=order_hash)
        return self._sign(order_bytes)
