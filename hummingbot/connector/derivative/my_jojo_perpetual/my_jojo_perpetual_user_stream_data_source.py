from typing import List, Optional

from furl import furl

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger


class MyJojoPerpetualUserStreamDataSource(UserStreamTrackerDataSource):

    _logger: Optional[HummingbotLogger] = None

    def __init__(
        self,
        auth: MyJojoPerpetualAuth,
        trading_pairs: List[str],
        connector,  # MyJojoPerpetualDerivative
        api_factory: WebAssistantsFactory,
        domain: str = CONSTANTS.DOMAIN,
    ):
        super().__init__()
        self._auth = auth
        self._trading_pairs: List[str] = trading_pairs
        self._connector = connector
        self._api_factory = api_factory
        self._domain = domain

    async def _connected_websocket_assistant(self) -> WSAssistant:
        # 直接在connect的时候拼接出完整url并完成授权
        ws: WSAssistant = await self._api_factory.get_ws_assistant()
        base_url = web_utils.wss_url(CONSTANTS.WS_SINGLE_URL, self._domain)
        url = furl(base_url)
        account = self._auth._public_key
        url /= f"account@{account}"
        timestamp = int(self._connector._time_synchronizer.time() * 1e3)
        url.args["timestamp"] = timestamp
        sign = self._auth.sign_message(**{"account": account, "timestamp": timestamp})
        url.args["signature"] = sign
        await ws.connect(url.url)
        return ws

    async def _subscribe_channels(self, websocket_assistant: WSAssistant):
        # 什么都不用做
        return
