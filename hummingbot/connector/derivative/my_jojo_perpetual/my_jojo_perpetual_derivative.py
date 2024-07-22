from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from bidict import bidict

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.constants import s_decimal_NaN
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_api_order_book_data_source import (
    MyJojoPerpetualAPIOrderBookDataSource,
)
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_user_stream_data_source import (
    MyJojoPerpetualUserStreamDataSource,
)
from hummingbot.connector.perpetual_derivative_py_base import PerpetualDerivativePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import combine_to_hb_trading_pair
from hummingbot.core.api_throttler.data_types import RateLimit
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, TradeType
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderUpdate, TradeUpdate
from hummingbot.core.data_type.perpetual_api_order_book_data_source import PerpetualAPIOrderBookDataSource
from hummingbot.core.data_type.trade_fee import TradeFeeBase
from hummingbot.core.data_type.user_stream_tracker_data_source import UserStreamTrackerDataSource
from hummingbot.core.utils.estimate_fee import build_trade_fee
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

if TYPE_CHECKING:
    from hummingbot.client.config.config_helpers import ClientConfigAdapter


class MyJojoPerpetualDerivative(PerpetualDerivativePyBase):

    web_utils = web_utils

    def __init__(
        self,
        client_config_map: "ClientConfigAdapter",
        public_key: str,
        private_key: str,
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        domain: str = CONSTANTS.DOMAIN,
    ):
        self._trading_pairs = trading_pairs
        self._trading_required = trading_required
        self._domain = domain
        self._public_key = public_key
        self._private_key = private_key

        super().__init__(client_config_map=client_config_map)

    @property
    def name(self) -> str:
        return self._domain

    @property
    def authenticator(self) -> MyJojoPerpetualAuth:
        return MyJojoPerpetualAuth(self._public_key, self._private_key)

    @property
    def rate_limits_rules(self) -> List[RateLimit]:
        return CONSTANTS.RATE_LIMITS

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def client_order_id_max_length(self) -> int:
        return CONSTANTS.MAX_ORDER_ID_LEN

    @property
    def client_order_id_prefix(self) -> str:
        return CONSTANTS.BROKER_ID

    @property
    def trading_rules_request_path(self) -> str:
        return CONSTANTS.EXCHANGE_INFO_URL

    @property
    def trading_pairs_request_path(self) -> str:
        return CONSTANTS.EXCHANGE_INFO_URL

    @property
    def check_network_request_path(self) -> str:
        return CONSTANTS.SERVER_TIME_PATH_URL

    @property
    def trading_pairs(self):
        return self._trading_pairs

    @property
    def is_cancel_request_in_exchange_synchronous(self) -> bool:
        return True

    @property
    def is_trading_required(self) -> bool:
        return self._trading_required

    @property
    def funding_fee_poll_interval(self) -> int:
        return 28800

    def _initialize_trading_pair_symbols_from_exchange_info(self, exchange_info: Dict[str, Any]):
        try:
            symbol_map = bidict()
            for market in exchange_info["markets"]:
                exchange_symbol = market["symbol"]
                base_asset, quote_asset = market["baseAssetName"], market["quoteAssetName"]
                trading_pair = combine_to_hb_trading_pair(base_asset, quote_asset)
                symbol_map[exchange_symbol] = trading_pair
            self._set_trading_pair_symbol_map(symbol_map)
        except Exception as e:
            self.logger().error(f"Error initializing trading pair symbol map: {str(e)}")

    async def _make_network_check_request(self):
        await self._api_get(path_url=self.check_network_request_path)

    def supported_order_types(self) -> List[OrderType]:
        return [OrderType.LIMIT, OrderType.MARKET]

    def supported_position_modes(self):
        return [PositionMode.ONEWAY, PositionMode.HEDGE]

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception):
        return False

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        raise NotImplementedError

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        raise NotImplementedError

    def _create_web_assistants_factory(self) -> WebAssistantsFactory:
        web_assistants_factory = web_utils.build_api_factory(
            throttler=self._throttler,
            time_synchronizer=self._time_synchronizer,
            domain=self.name,
            auth=self.authenticator,
        )
        return web_assistants_factory

    def _create_order_book_data_source(self) -> PerpetualAPIOrderBookDataSource:
        source = MyJojoPerpetualAPIOrderBookDataSource(
            trading_pairs=self.trading_pairs,
            connector=self,
            api_factory=self._web_assistants_factory,
            domain=self.name,
        )
        return source

    def _create_user_stream_data_source(self) -> UserStreamTrackerDataSource:
        source = MyJojoPerpetualUserStreamDataSource(
            self.authenticator, self.trading_pairs, self, self._web_assistants_factory, domain=self.name
        )
        return source

    async def _place_order(
        self,
        order_id: str,
        trading_pair: str,
        amount: Decimal,
        trade_type: TradeType,
        order_type: OrderType,
        price: Decimal,
        position_action: PositionAction = PositionAction.NIL,
        **kwargs,
    ) -> Tuple[str, float]:
        pass

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        pass

    async def _set_trading_pair_leverage(self, trading_pair: str, leverage: int) -> Tuple[bool, str]:
        pass

    async def _trading_pair_position_mode_set(self, mode: PositionMode, trading_pair: str) -> Tuple[bool, str]:
        pass

    async def _fetch_last_fee_payment(self, trading_pair: str) -> Tuple[float, Decimal, Decimal]:
        pass

    def _get_fee(
        self,
        base_currency: str,
        quote_currency: str,
        order_type: OrderType,
        order_side: TradeType,
        position_action: PositionAction,
        amount: Decimal,
        price: Decimal = s_decimal_NaN,
        is_maker: Optional[bool] = None,
    ) -> TradeFeeBase:
        is_maker = is_maker or False
        fee = build_trade_fee(
            self.name,
            is_maker,
            base_currency=base_currency,
            quote_currency=quote_currency,
            order_type=order_type,
            order_side=order_side,
            amount=amount,
            price=price,
        )
        return fee

    async def _update_trading_fees(self):
        # 费用不会变化
        return

    async def _user_stream_event_listener(self):
        async for event_message in self._iter_user_event_queue():
            pass

    async def _update_positions(self):
        pass

    async def _update_balances(self):
        pass

    async def _format_trading_rules(self, exchange_info_dict: Dict[str, Any]) -> List[TradingRule]:
        raw_info = exchange_info_dict["markets"]
        trading_rules = []
        for info in raw_info:
            trading_pair = self.trading_pair_associated_to_exchange_symbol(info["symbol"])
            filters = {v["filterType"]: v for v in info["filters"]}
            trading_rule = TradingRule(
                trading_pair,
                min_price_increment=Decimal(filters["PRICE_FILTER"]["tickSize"]),
                min_base_amount_increment=Decimal(filters["AMOUNT_FILTER"]["stepSize"]),
                buy_order_collateral_token=info["baseAssetName"],
                sell_order_collateral_token=info["baseAssetName"],
            )
            trading_rules.append(trading_rule)
        return trading_rules

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        pass

    async def _request_order_status(self, tracked_order: InFlightOrder) -> OrderUpdate:
        pass

    def get_buy_collateral_token(self, trading_pair: str) -> str:
        trading_rule: TradingRule = self._trading_rules[trading_pair]
        return trading_rule.buy_order_collateral_token

    def get_sell_collateral_token(self, trading_pair: str) -> str:
        trading_rule: TradingRule = self._trading_rules[trading_pair]
        return trading_rule.sell_order_collateral_token
