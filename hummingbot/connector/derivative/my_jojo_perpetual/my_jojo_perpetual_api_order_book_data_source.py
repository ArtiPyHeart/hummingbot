import asyncio
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional

import numpy as np

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.core.data_type.common import TradeType
from hummingbot.core.data_type.funding_info import FundingInfo, FundingInfoUpdate
from hummingbot.core.data_type.order_book_message import OrderBookMessage, OrderBookMessageType
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
        connector,  # MyJojoPerpetualDerivative
        api_factory: WebAssistantsFactory,
        domain: str = CONSTANTS.DOMAIN,
    ):
        super().__init__(trading_pairs)
        self._connector = connector
        self._api_factory: WebAssistantsFactory = api_factory
        self._domain = domain
        self._trading_pairs: List[str] = trading_pairs

        self._latest_order_book_snapshots: Dict[str, OrderBookMessage] = {}
        self._latest_funding_info: Dict[str, FundingInfo] = {}

    async def get_latest_funding_info(self, trading_pair: str) -> Optional[FundingInfo]:
        return self._latest_funding_info.get(trading_pair)

    async def _connected_websocket_assistant(self) -> WSAssistant:
        ws_url = web_utils.wss_url(CONSTANTS.WS_COMBINED_URL, self._domain)
        ws: WSAssistant = await self._api_factory.get_ws_assistant()
        await ws.connect(ws_url)
        return ws

    async def get_last_traded_prices(self, trading_pairs: List[str], domain: Optional[str] = None) -> Dict[str, float]:
        tasks = [self._get_last_traded_price_for_single_pair(trading_pair, domain) for trading_pair in trading_pairs]
        results = await asyncio.gather(*tasks)
        return dict(zip(trading_pairs, results))

    async def _get_last_traded_price_for_single_pair(self, trading_pair: str, domain: Optional[str] = None) -> float:
        url = web_utils.public_rest_url(CONSTANTS.TRADES_URL, domain=domain)
        exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair)
        params = {"marketId": exchange_symbol, "limit": 1}
        raw_response = await self._connector._api_get(url, params=params)
        return float(raw_response[0]["price"])

    async def _subscribe_channels(self, ws: WSAssistant):
        payload = {
            "id": 1,
            "method": "SUBSCRIBE",
            "params": [],
        }
        for trading_pair in self._trading_pairs:
            exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair)
            market_channel = f"{exchange_symbol}@market"
            orderbook_channel = f"{exchange_symbol}@orderbook"
            trade_channel = f"{exchange_symbol}@trade"
            payload["params"].extend([market_channel, orderbook_channel, trade_channel])

        await ws.send(WSJSONRequest(payload=payload))
        self.logger().info(f"Subscribed: {'|'.join(payload['params'])}")

    async def _parse_funding_info_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """
        {"stream":"btcusdc@market","data":{"fundingRate":"0.0001","nextFundingTime":1721318400000,"markPrice":"63957.19635104","offchainMarkPrice":"63933.32516509","offchainMarkPrice24HAgo":"64984.01218979","indexPrice":"63975.45818013","liquidationThreshold":"0.01","liquidationPriceOff":"0.005","24hVolume":"359.875166","24hQuoteVolume":"23224862.2791608","openInterest":"17.9197695","price24HAgo":"64928.02","lastTradePrice":"63910.73"}}
        """
        exchange_symbol = raw_message["stream"].split("@")[0]
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)
        funding_raw_data = raw_message["data"]
        funding_info: FundingInfoUpdate = FundingInfoUpdate(
            trading_pair=trading_pair,
            index_price=Decimal(funding_raw_data["indexPrice"]),
            mark_price=Decimal(funding_raw_data["markPrice"]),
            next_funding_utc_timestamp=int(funding_raw_data["nextFundingTime"] / 1000),
            rate=Decimal(funding_raw_data["fundingRate"]),
        )
        message_queue.put_nowait(funding_info)

    async def _parse_order_book_diff_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """
        {"stream":"btcusdc@orderbook","data":{"event":"update","beginSequence":165851954,"endSequence":165851988,"bids":[["63908.66","1.0953"],["63907.06","1.1714"],["63905.46","1.1886"],["63903.87","1.2061"],["63902.27","1.2238"],["63900.67","1.2418"],["63899.07","1.26"],["63897.48","1.2785"],["63879.27","0.9784"],["63876.89","0"],["63874.97","0"],["63869.69","0.9786"],["63862.02","0.9787"],["63840.49","0"],["63222.16","4.6503"],["56371.42","0"],["56369.69","0"],["56342.85","0"],["56114.28","0"],["56100","0"],["56049.17","0"],["56000","0"],["55857.14","0"],["55800","0"]],"asks":[["73527.36","0"],["73500","0"],["73357.5","0"],["73200","0"],["73036.97","0"],["72900","0"],["72799.39","0"],["72716.45","0"],["72600","0"],["72395.92","0"],["72300","0"],["72079.76","0"],["63951.49","0.9773"],["63949.57","0.9773"],["63947.66","0.9774"],["63945.74","0.9774"],["63943.82","1.3347"],["63942.22","1.3154"],["63940.62","1.2964"],["63939.02","1.2777"],["63937.42","1.2593"],["63935.83","1.2411"],["63934.23","1.2232"],["63932.63","1.2055"],["63931.03","1.1881"],["63929.43","1.171"],["63927.83","1.095"],["63922.62","0"],["63921.02","0"],["63919.42","0"]]}}
        """
        exchange_symbol = raw_message["stream"].split("@")[0]
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)
        bids = np.array(raw_message["data"]["bids"], dtype=float).tolist()
        asks = np.array(raw_message["data"]["asks"], dtype=float).tolist()
        order_book_message: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.DIFF,
            {"trading_pair": trading_pair, "update_id": raw_message["data"]["endSequence"], "bids": bids, "asks": asks},
            timestamp=self._connector._time_synchronizer.time(),
        )
        message_queue.put_nowait(order_book_message)

    async def _parse_order_book_snapshot_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """
        {"data":{"event":"snapshot","sequence":165851953,"bids":[["63897.91","0.9781"],["63895.99","0.9782"],["63894.08","0.9782"],["63893.86","1.0956"],["63892.26","1.1716"],["63891.56","1.0956"],["63891.15","0.9782"],["63890.67","1.1889"],["63889.96","1.1717"],["63889.23","0.9783"],["63889.07","1.2063"],["63888.37","1.1889"],["63887.47","1.2241"],["63887.32","0.9783"],["63886.77","1.2064"],["63886.73","0.9783"],["63886.47","1.2241"],["63885.87","1.2421"],["63885.17","1.2241"],["63884.87","1.2421"],["63884.28","1.2603"],["63883.57","1.2421"],["63881.98","1.2604"],["63881.68","1.2789"],["63880.38","1.2789"],["63880.08","1.2977"],["63879.49","1.3167"],["63878.78","1.2977"],["63876.89","1.3361"],["63874.97","0.9785"],["63874.06","0.9785"],["63873.06","0.9785"],["63872.14","0.9785"],["63871.14","0.9785"],["63869.22","0.9786"],["63868.31","0.9786"],["63867.31","0.9786"],["63866.01","0.9786"],["63865.39","0.9786"],["63863.48","0.9787"],["63861.56","0.9787"],["63860.26","0.9787"],["63855.81","0.9788"],["63853.9","0.9788"],["63852.98","0.9788"],["63847.24","0.9789"],["63844.32","0.9789"],["63842.41","0.979"],["63841.49","0.979"],["63841.11","0.979"],["63840.49","0.979"],["63838.57","0.979"],["63818.85","0.9793"],["63812.31","0.9794"],["63750","0.000661"],["63600","0.0008"],["63571.42","0.003761"],["63543.67","0.002603"],["63542.85","0.001153"],["63500","0.001089"],["63421.23","0.000405"],["63333.33","0.0004"],["63314.28","0.003761"],["63300","0.0004"],["63292.7","0.002603"],["63257.5","0.000974"],["63254.21","4.6479"],["63250","0.000661"],["63206.53","4.6514"],["63200","0.001153"],["63100.71","0.000405"],["63066.66","0.0004"],["63057.14","0.003761"],["63041.74","0.002603"],["63000","0.001489"],["62857.14","0.001153"],["62800","0.0004"],["62799.99","0.003761"],["62790.77","0.002603"],["62780.19","0.000405"],["62778.75","0.000974"],["62750","0.000661"],["62700","0.0004"],["62542.85","0.003761"],["62539.81","0.002603"],["62533.33","0.0004"],["62514.28","0.001153"],["62500","0.001089"],["62459.66","0.000405"],["62450","0.040832"],["62400","0.0004"],["62300","0.000974"],["62288.84","0.002603"],["62285.71","0.003761"],["62266.66","0.0004"],["62250","0.000661"],["62171.42","0.001153"],["62139.14","0.000405"],["62100","0.0004"],["62028.57","0.003761"],["62000","0.001489"],["61961.15","4.7449"],["61828.57","0.001153"],["61818.61","0.000405"],["61800","0.0004"],["61771.42","0.003761"],["61750","0.000661"],["61514.28","0.003761"],["61500","0.001489"],["61498.09","0.000405"],["61485.71","0.001153"],["61257.14","0.003761"],["61250","0.000661"],["61200","0.002042"],["61177.56","0.000405"],["61142.85","0.001153"],["61000","0.002731"],["60999.99","0.003761"],["60900","0.0004"],["60857.04","0.000405"],["60800","0.002795"],["60750","0.000661"],["60742.85","0.003761"],["60600","0.002042"],["60536.51","0.000405"],["60500","0.001089"],["60485.71","0.003761"],["60457.14","0.001153"],["60400","0.001642"],["60300","0.0004"],["60228.57","0.003761"],["60215.99","0.000405"],["60139.89","4.8886"],["60114.28","0.001153"],["60000","0.04166"],["59971.42","0.003761"],["59895.46","0.000405"],["59771.42","0.001153"],["59714.28","0.003761"],["59700","0.0004"],["59574.94","0.000405"],["59500","0.000428"],["59457.14","0.003761"],["59428.57","0.001153"],["59400","0.0004"],["59254.41","0.000405"],["59199.99","0.003761"],["59100","0.0004"],["59085.71","0.001153"],["59000","0.000428"],["58954.01","4.9869"],["58942.85","0.003761"],["58933.89","0.000405"],["58800","0.0004"],["58742.85","0.001153"],["58685.71","0.003761"],["58613.37","0.000405"],["58500","0.000828"],["58428.57","0.003761"],["58400","0.001153"],["58292.84","0.000405"],["58200","0.0004"],["58171.42","0.003761"],["58057.14","0.001153"],["58000","0.000428"],["57972.32","0.000405"],["57914.28","0.003761"],["57900","0.0004"],["57836.01","5.0833"],["57792.42","5.0872"],["57714.28","0.001153"],["57657.14","0.003761"],["57651.79","0.000405"],["57600","0.0004"],["57500","0.000428"],["57399.99","0.003761"],["57371.42","0.001153"],["57331.27","0.000405"],["57300","0.0004"],["57142.85","0.003761"],["57028.57","0.001153"],["57010.74","0.000405"],["57000","0.000828"],["56885.71","0.003761"],["56700","0.0004"],["56690.22","0.000405"],["56685.71","0.001153"],["56654.61","5.1893"],["56628.57","0.003761"],["56500","0.000428"],["56400","0.0004"],["56371.42","0.003761"],["56369.69","0.000405"],["56342.85","0.001153"],["56114.28","0.003761"],["56100","0.0004"],["56049.17","0.000405"],["56000","0.001581"],["55857.14","0.003761"],["55800","0.0004"]],"asks":[["73527.36","3.9985"],["73500","0.0004"],["73357.5","0.000405"],["73200","0.0004"],["73036.97","0.000405"],["72900","0.0004"],["72799.39","4.0385"],["72716.45","0.000405"],["72600","0.0004"],["72395.92","0.000405"],["72300","0.0004"],["72079.76","4.0788"],["72078.63","4.0789"],["72075.4","0.000405"],["72000","0.0004"],["71754.87","0.000405"],["71700","0.0004"],["71434.35","0.000405"],["71400","0.0004"],["71113.82","0.000405"],["71100","0.0004"],["70800","0.0004"],["70793.3","0.000405"],["70658.44","4.1609"],["70657.01","4.1609"],["70500","0.0004"],["70472.78","0.000405"],["70200","0.0004"],["70152.25","0.000405"],["70000","0.000428"],["69999.99","0.003761"],["69958.88","4.2025"],["69900","0.0004"],["69831.73","0.000405"],["69777","0.429941"],["69742.85","0.003761"],["69600","0.0004"],["69511.2","0.000405"],["69500","0.000428"],["69485.71","0.003761"],["69318.49","4.2413"],["69300","0.0004"],["69266.24","4.2445"],["69228.57","0.003761"],["69190.68","0.000405"],["69000","0.000828"],["68971.42","0.003761"],["68870.15","0.000405"],["68714.28","0.003761"],["68700","0.0004"],["68633.91","4.2836"],["68549.63","0.000405"],["68500","0.000428"],["68457.14","0.003761"],["68400","0.0004"],["68229.1","0.000405"],["68199.99","0.003761"],["68100","0.0004"],["68000","0.001581"],["67942.85","0.003761"],["67908.58","0.000405"],["67902.53","4.3297"],["67901.47","4.3298"],["67800","0.0004"],["67685.71","0.003761"],["67657.14","0.001153"],["67588.05","0.000405"],["67500","0.000828"],["67428.57","0.003761"],["67314.28","0.001153"],["67267.53","0.000405"],["67200","0.0004"],["67171.42","0.003761"],["67000","0.000428"],["66971.42","0.001153"],["66947","0.000405"],["66914.28","0.003761"],["66900","0.0004"],["66657.14","0.003761"],["66628.57","0.001153"],["66626.48","0.000405"],["66600","0.0004"],["66563.58","4.4168"],["66500","0.000428"],["66399.99","0.003761"],["66305.96","0.000405"],["66300","0.0004"],["66285.71","0.001153"],["66142.85","0.003761"],["66130","0.000974"],["66000","0.002732"],["65985.43","0.000405"],["65955.92","4.4575"],["65942.85","0.001153"],["65885.71","0.003761"],["65846.15","0.000443"],["65750","0.000661"],["65733.33","0.0004"],["65714.28","0.0004"],["65700","0.0004"],["65692.3","0.000443"],["65664.91","0.000405"],["65651.25","0.000974"],["65628.57","0.003761"],["65600","0.001153"],["65551.39","0.002603"],["65538.46","0.000443"],["65500","0.001089"],["65466.66","0.0004"],["65428.57","0.0004"],["65400","0.0004"],["65384.61","0.000443"],["65371.42","0.003761"],["65344.38","0.000405"],["65300.43","0.002603"],["65257.14","0.001153"],["65252.06","4.5056"],["65250","0.000661"],["65230.76","0.000443"],["65200","0.0004"],["65172.5","0.000974"],["65142.85","0.0004"],["65114.28","0.003761"],["65100","0.1004"],["65076.92","0.000443"],["65049.46","0.002603"],["65023.86","0.000405"],["65000","0.001089"],["64933.33","0.0004"],["64923.07","0.000443"],["64914.28","0.001153"],["64857.14","0.004161"],["64800","0.0004"],["64798.5","0.002603"],["64769.23","0.000443"],["64750","0.000661"],["64703.33","0.000405"],["64693.75","0.000974"],["64666.66","0.0004"],["64615.38","0.000443"],["64599.99","0.003761"],["64571.42","0.001553"],["64547.53","0.002603"],["64500","0.001489"],["64461.53","0.000443"],["64400","0.0004"],["64382.81","0.000405"],["64342.85","0.003761"],["64307.69","0.000443"],["64296.57","0.002603"],["64285.71","0.0004"],["64250","0.000661"],["64228.57","0.001153"],["64215","0.000974"],["64200","0.0004"],["64153.84","0.000443"],["64133.33","0.0004"],["64085.71","0.003761"],["64062.28","0.000405"],["64045.6","0.002603"],["64010.79","0.9764"],["64000.87","0.9765"],["63998.95","0.9766"],["63997.03","0.9766"],["63995.11","0.9766"],["63993.51","0.9767"],["63991.59","0.9767"],["63989.67","0.9767"],["63987.75","0.9767"],["63985.83","0.9768"],["63983.91","0.9768"],["63982.58","0.9768"],["63980.07","0.9769"],["63978.15","0.9769"],["63976.23","1.334"],["63974.63","1.2957"],["63973.04","1.277"],["63973.03","1.2958"],["63971.44","1.2586"],["63971.06","0.977"],["63969.84","1.2404"],["63968.24","1.2225"],["63966.64","1.2049"],["63965.04","1.1875"],["63963.44","1.1703"],["63961.84","1.0944"],["63961.62","0.9771"],["63960.62","0.9772"],["63960.24","1.0944"],["63959.55","0.9772"],["63957.63","0.9772"],["63948.19","0.9774"],["63942.44","0.9774"],["63929.01","1.335"],["63927.41","1.3157"],["63925.82","1.2967"],["63924.22","1.278"],["63922.62","1.2596"],["63921.02","1.2414"],["63919.42","1.2235"]]},"stream":"btcusdc@orderbook"}
        """
        exchange_symbol = raw_message["stream"].split("@")[0]
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)
        bids = np.array(raw_message["data"]["bids"], dtype=float).tolist()
        asks = np.array(raw_message["data"]["asks"], dtype=float).tolist()
        order_book_message: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            {"trading_pair": trading_pair, "update_id": raw_message["data"]["sequence"], "bids": bids, "asks": asks},
            timestamp=self._connector._time_synchronizer.time(),
        )
        message_queue.put_nowait(order_book_message)

    async def _parse_trade_message(self, raw_message: Dict[str, Any], message_queue: asyncio.Queue):
        """
        Received: {"stream":"btcusdc@trades","data":{"id":200299297171968,"price":"66657.35","amount":"0.184159","quoteAmount":"12275.55091865","time":1721461195599,"isBuyerMaker":false,"status":"CREATED"}}
        """
        exchange_symbol = raw_message["stream"].split("@")[0]
        trading_pair = await self._connector.trading_pair_associated_to_exchange_symbol(exchange_symbol)

        trade_message: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.TRADE,
            {
                "trading_pair": trading_pair,
                "trade_id": raw_message["data"]["id"],
                "price": float(raw_message["data"]["price"]),
                "amount": float(raw_message["data"]["amount"]),
                "trade_type": TradeType.BUY if raw_message["data"]["isBuyerMaker"] else TradeType.SELL,
            },
            timestamp=raw_message["data"]["time"] / 1000,
        )
        message_queue.put_nowait(trade_message)

    def _channel_originating_message(self, event_message: Dict[str, Any]) -> str:
        channel = ""
        if "stream" in event_message:
            if event_message["stream"].endswith("@orderbook"):
                if event_message["data"]["event"] == "snapshot":
                    channel = self._snapshot_messages_queue_key
                elif event_message["data"]["event"] == "update":
                    channel = self._diff_messages_queue_key
            elif event_message["stream"].endswith("@trades"):
                channel = self._trade_messages_queue_key
            elif event_message["stream"].endswith("@market"):
                channel = self._funding_info_messages_queue_key
        return channel

    async def _process_message_for_unknown_channel(
        self, event_message: Dict[str, Any], websocket_assistant: WSAssistant
    ):
        """
        Processes a message coming from a not identified channel.
        Does nothing by default but allows subclasses to reimplement

        :param event_message: the event received through the websocket connection
        :param websocket_assistant: the websocket connection to use to interact with the exchange
        """
        return

    async def get_funding_info(self, trading_pair: str) -> FundingInfo:
        rest_api_resp: Optional[FundingInfo] = await self._connector.get_funding_info_from_rest_api(trading_pair)
        while rest_api_resp is None:
            self.logger().warning(
                "MyJojoPerpetualAPIOrderBookDataSource.get_funding_info cannot get funding info from REST API"
            )
            await asyncio.sleep(2)
            rest_api_resp: FundingInfo = await self._connector.get_funding_info_from_rest_api(trading_pair)
        return rest_api_resp

    async def _order_book_snapshot(self, trading_pair: str) -> OrderBookMessage:
        exchange_symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair)
        params = {"marketId": exchange_symbol, "limit": 1000}
        raw_orderbook_msg = await self._connector._api_get(path_url=CONSTANTS.ORDERBOOK_URL, params=params)
        order_book_message: OrderBookMessage = OrderBookMessage(
            OrderBookMessageType.SNAPSHOT,
            {
                "trading_pair": trading_pair,
                "update_id": raw_orderbook_msg["sequence"],
                "bids": raw_orderbook_msg["bids"],
                "asks": raw_orderbook_msg["asks"],
            },
            timestamp=self._connector._time_synchronizer.time(),
        )
        return order_book_message
        # while True:
        #     try:
        #         order_book_message: OrderBookMessage = await self._message_queue[
        #             self._snapshot_messages_queue_key
        #         ].get()
        #         # store orderbook message first
        #         self._latest_order_book_snapshots[order_book_message.trading_pair] = order_book_message
        #         # return the order book snapshot if it matches the trading pair
        #         order_book_snapshot = self._latest_order_book_snapshots.get(trading_pair)
        #         if order_book_snapshot is not None:
        #             return order_book_snapshot
        #         else:
        #             continue
        #     except:
        #         self.logger().error(f"Error getting order book snapshot for {trading_pair}: {traceback.format_exc()}")
