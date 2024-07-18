import asyncio
from typing import Any, Dict, List, Mapping, Optional

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_derivative import MyJojoPerpetualDerivative
from hummingbot.core.data_type.funding_info import FundingInfo
from hummingbot.core.data_type.order_book_message import OrderBookMessage
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.logger import HummingbotLogger


class MyJojoPerpetualAPIOrderBookDataSource(PerpetualAPIOrderBookDataSource):
    _bpobds_logger: Optional[HummingbotLogger] = None
    _trading_pair_symbol_map: Dict[str, Mapping[str, str]] = {}
    _mapping_initialization_lock = asyncio.Lock()

    def __init__(
        self,
        trading_pairs: List[str],
        connector: "MyJojoPerpetualDerivative",
        api_factory: WebAssistantsFactory,
        domain: str = CONSTANTS.DOMAIN,
    ):
        super().__init__(trading_pairs)
        self._connector: MyJojoPerpetualDerivative = connector
        self._api_factory: WebAssistantsFactory = api_factory
        self._domain = domain
        self._trading_pairs: List[str] = trading_pairs

    async def get_last_traded_prices(self, trading_pairs: List[str], domain: Optional[str] = None) -> Dict[str, float]:
        raise NotImplementedError

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise NotImplementedError

    async def _parse_order_book_diff_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise NotImplementedError

    async def _parse_order_book_snapshot_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise NotImplementedError

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        raise NotImplementedError

    async def _connected_websocket_assistant(self) -> WSAssistant:
        ws_url = web_utils.wss_url(CONSTANTS.WS_COMBINED_URL, self._domain)
        ws: WSAssistant = await self._api_factory.get_ws_assistant()
        await ws.connect(ws_url)
        return ws

    async def _subscribe_channels(self, ws: WSAssistant):
        payload = {
            "id": 1,
            "method": "SUBSCRIBE",
            "params": [],
        }
        for trading_pair in self._trading_pairs:
            exchange_symbol = self._connector.exchange_symbol_associated_to_pair(trading_pair)
            market_channel = f"{exchange_symbol}@market"
            orderbook_channel = f"{exchange_symbol}@orderbook"
            trade_channel = f"{exchange_symbol}@trade"
            payload["params"].extend([market_channel, orderbook_channel, trade_channel])

        await ws.send(WSJSONRequest(payload=payload))
        self.logger().info(f"Subscribed: {'|'.join(payload['params'])}")

    def _channel_originating_message(self, event_message: Dict[str, Any]) -> str:
        raise NotImplementedError

    async def _process_message_for_unknown_channel(
        self, event_message: Dict[str, Any], websocket_assistant: WSAssistant
    ):
        """
        Processes a message coming from a not identified channel.
        Does nothing by default but allows subclasses to reimplement

        :param event_message: the event received through the websocket connection
        :param websocket_assistant: the websocket connection to use to interact with the exchange
        """
        pass

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        raise NotImplementedError

    async def _parse_funding_info_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        raise NotImplementedError
