import asyncio
import logging
from typing import Dict, Optional
from urllib.parse import urljoin

import numpy as np

from hummingbot.core.network_iterator import NetworkStatus
from hummingbot.core.utils.async_utils import safe_ensure_future
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.ws_assistant import WSAssistant
from hummingbot.data_feed.candles_feed.candles_base import CandlesBase
from hummingbot.data_feed.candles_feed.my_jojo_perpetual import constants as CONSTANTS
from hummingbot.logger import HummingbotLogger


class MyJojoPerpetualCandles(CandlesBase):
    _logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._logger is None:
            cls._logger = logging.getLogger(__name__)
        return cls._logger

    def __init__(self, trading_pair: str, interval: str = "1M", max_records: int = 150):
        super().__init__(trading_pair, interval, max_records)

    @property
    def name(self):
        return f"my_jojo_perpetual_{self._trading_pair}"

    @property
    def rest_url(self):
        return CONSTANTS.REST_URL

    @property
    def wss_url(self):
        return CONSTANTS.WSS_URL

    @property
    def health_check_url(self):
        return urljoin(self.rest_url, CONSTANTS.HEALTH_CHECK_ENDPOINT)

    @property
    def candles_url(self):
        return urljoin(self.rest_url, CONSTANTS.CANDLES_ENDPOINT)

    @property
    def rete_limits(self):
        return CONSTANTS.RATE_LIMITS

    @property
    def intervals(self):
        return CONSTANTS.INTERVALS

    async def check_network(self) -> NetworkStatus:
        rest_assistant = await self._api_factory.get_rest_assistant()
        await rest_assistant.execute_request(
            url=self.health_check_url, throttler_limit_id=CONSTANTS.HEALTH_CHECK_ENDPOINT
        )
        return NetworkStatus.CONNECTED

    def get_exchange_trading_pair(self, trading_pair):
        return trading_pair.replace("-", "").lower()

    async def fetch_candles(
        self, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: Optional[int] = 500
    ):
        rest_assistant = await self._api_factory.get_rest_assistant()
        params = {
            "marketId": self._ex_trading_pair,
            "interval": self.interval,
            "limit": limit,
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        candles = await rest_assistant.execute_request(
            url=self.candles_url,
            throttler_limit_id=CONSTANTS.CANDLES_ENDPOINT,
            params=params,
        )
        new_hb_candles = [
            [
                int(i["time"]),
                float(i["open"]),
                float(i["high"]),
                float(i["low"]),
                float(i["close"]),
                float(i["volume"]),
                float(i["volume"])
                * ((float(i["high"]) + float(i["low"]) + float(i["close"])) / 3),  # quote_asset_volume
                0,  # n_trades
                0,  # taker_buy_base_volume
                0,  # taker_buy_quote_volume
            ]
            for i in candles
        ]
        return np.array(new_hb_candles)

    async def fill_historical_candles(self):
        max_request_needed = (self._candles.maxlen // 1000) + 1
        requests_executed = 0
        while not self.ready:
            missing_records = self._candles.maxlen - len(self._candles)
            end_timestamp = int(self._candles[0][0])
            try:
                if requests_executed < max_request_needed:
                    # we have to add one more since, the last row is not going to be included
                    candles = await self.fetch_candles(end_time=end_timestamp, limit=missing_records + 1)
                    # we are computing again the quantity of records again since the websocket process is able to
                    # modify the deque and if we extend it, the new observations are going to be dropped.
                    missing_records = self._candles.maxlen - len(self._candles)
                    self._candles.extendleft(candles[-(missing_records + 1) : -1][::-1])  # noqa: E203
                    requests_executed += 1
                else:
                    self.logger().error(
                        f"There is no data available for the quantity of candles requested for {self.name}."
                    )
                    raise
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger().exception(
                    "Unexpected error occurred when getting historical klines. Retrying in 1 seconds...",
                )
                await self._sleep(1.0)

    async def _subscribe_channels(self, ws: WSAssistant):
        try:
            candle_params = [f"{self._ex_trading_pair}@kline{self.interval}"]
            payload = {
                "id": 1,
                "method": "SUBSCRIBE",
                "params": candle_params,
            }
            subscribe_candles_request: WSJSONRequest = WSJSONRequest(payload=payload)
            await ws.send(subscribe_candles_request)
            self.logger().info("Subscribed to public klines...")
        except asyncio.CancelledError:
            raise
        except Exception:
            self.logger().error("Unexpected error occurred subscribing to public klines...", exc_info=True)
            raise

    async def _process_websocket_messages(self, websocket_assistant: WSAssistant):
        async for ws_response in websocket_assistant.iter_messages():
            resp: Dict = ws_response.data
            if "data" in resp:
                data = resp["data"]
                for d in data:
                    timestamp_ms = int(d["time"])
                    kline_open = float(d["open"])
                    kline_high = float(d["high"])
                    kline_low = float(d["low"])
                    kline_close = float(d["close"])
                    kline_volume = float(d["volume"])
                    kline_quote_asset_volume = float(d["volume"]) * (
                        (float(d["high"]) + float(d["low"]) + float(d["close"])) / 3
                    )
                    n_trades = 0
                    taker_buy_base_volume = 0
                    taker_buy_quote_volume = 0
                    if len(self._candles) == 0:
                        self._candles.append(
                            np.array(
                                [
                                    timestamp_ms,
                                    kline_open,
                                    kline_high,
                                    kline_low,
                                    kline_close,
                                    kline_volume,
                                    kline_quote_asset_volume,
                                    n_trades,
                                    taker_buy_base_volume,
                                    taker_buy_quote_volume,
                                ]
                            )
                        )
                        safe_ensure_future(self.fill_historical_candles())
                    elif timestamp_ms > int(self._candles[-1][0]):
                        self._candles.append(
                            np.array(
                                [
                                    timestamp_ms,
                                    kline_open,
                                    kline_high,
                                    kline_low,
                                    kline_close,
                                    kline_volume,
                                    kline_quote_asset_volume,
                                    n_trades,
                                    taker_buy_base_volume,
                                    taker_buy_quote_volume,
                                ]
                            ).astype(float)
                        )
                    elif timestamp_ms == int(self._candles[-1][0]):
                        self._candles.pop()
                        self._candles.append(
                            np.array(
                                [
                                    timestamp_ms,
                                    kline_open,
                                    kline_high,
                                    kline_low,
                                    kline_close,
                                    kline_volume,
                                    kline_quote_asset_volume,
                                    n_trades,
                                    taker_buy_base_volume,
                                    taker_buy_quote_volume,
                                ]
                            ).astype(float)
                        )
