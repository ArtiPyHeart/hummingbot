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
from hummingbot.connector.derivative.position import Position
from hummingbot.connector.perpetual_derivative_py_base import PerpetualDerivativePyBase
from hummingbot.connector.trading_rule import TradingRule
from hummingbot.connector.utils import combine_to_hb_trading_pair
from hummingbot.core.api_throttler.data_types import RateLimit
from hummingbot.core.data_type.common import OrderType, PositionAction, PositionMode, PositionSide, TradeType
from hummingbot.core.data_type.funding_info import FundingInfo
from hummingbot.core.data_type.in_flight_order import InFlightOrder, OrderState, OrderUpdate, TradeUpdate
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

        self._raw_balances_websocket = None
        self._raw_positions_websocket = None
        self._raw_funding_fees_websocket: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return self._domain

    @property
    def authenticator(self) -> MyJojoPerpetualAuth:
        return MyJojoPerpetualAuth(self._public_key, self._private_key, self._time_synchronizer)

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

    async def get_kline_from_rest_api(self, trading_pair: str, interval: str = "1M"):
        full_url = web_utils.public_rest_url(CONSTANTS.KLINES_URL, domain=self.name)
        exchange_symbol = await self.exchange_symbol_associated_to_pair(trading_pair)
        request_params = {"marketId": exchange_symbol, "interval": interval, "limit": 1}
        response = await self._api_get(path_url=full_url, params=request_params)
        if isinstance(response, list) and len(response) > 0:
            """
            {
                "time": 1656029700000,
                "open": "2001",
                "close": "2001",
                "high": "2001",
                "low": "2001",
                "volume": "0"
            }
            """
            return response[0]
        else:
            self.logger().error(f"Error fetching kline: {response = }")
            return None

    async def get_funding_info_from_rest_api(self, trading_pair: str) -> Optional[FundingInfo]:
        full_url = web_utils.public_rest_url(CONSTANTS.FUNDING_RATE_URL, domain=self.name)
        exchange_symbol = await self.exchange_symbol_associated_to_pair(trading_pair)
        request_params = {"marketId": exchange_symbol, "limit": 1}
        response = await self._api_get(path_url=full_url, params=request_params)
        kline = await self.get_kline_from_rest_api(trading_pair)
        if isinstance(response, list) and len(response) > 0 and kline:
            """
            {
                "marketId": "btcusdc",
                "fundingRate": "0.0000026",
                "fundingTime": 1655902360000
            }
            """
            resp = response[0]
            funding_info = FundingInfo(
                trading_pair=trading_pair,
                index_price=Decimal(kline["close"]),
                mark_price=Decimal(kline["close"]),
                next_funding_utc_timestamp=resp["fundingTime"] / 1000 + self.funding_fee_poll_interval,
                rate=Decimal(resp["fundingRate"]),
            )
            return funding_info
        else:
            self.logger().error(f"Error fetching funding rate: {response = }")
            return None

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
        return [PositionMode.ONEWAY]

    def _is_request_exception_related_to_time_synchronizer(self, request_exception: Exception):
        return False

    def _is_order_not_found_during_status_update_error(self, status_update_exception: Exception) -> bool:
        if status_update_exception is CONSTANTS.JojoOrderNotFoundError:
            return True
        return False

    def _is_order_not_found_during_cancelation_error(self, cancelation_exception: Exception) -> bool:
        if cancelation_exception is CONSTANTS.JojoOrderNotFoundError:
            return True
        return False

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
        exchange_symbol = await self.exchange_symbol_associated_to_pair(trading_pair)
        time_in_force = kwargs.get("time_in_force", CONSTANTS.TimeInForce.GTC)
        expiration = kwargs.get("expiration", None)
        side = "BUY" if trade_type is TradeType.BUY else "SELL"
        order_type = "LIMIT" if order_type is OrderType.LIMIT else "MARKET"
        build_info = await self._place_order_build_order(
            exchange_symbol=exchange_symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            time_in_force=time_in_force,
            expiration=expiration,
        )
        order_url = web_utils.private_rest_url(CONSTANTS.ORDER_URL, domain=self.name)
        request_params = {
            "marketId": exchange_symbol,
            "side": side,
            "orderType": order_type,
            "amount": amount,
            "price": price,
            "timeInForce": time_in_force.value,
            "orderHash": build_info["orderHash"],
            "info": build_info["order"]["info"],
            "gasFeeQuotation": build_info["gasFeeQuotation"],
        }
        if time_in_force == CONSTANTS.TimeInForce.GTT:
            if expiration is None:
                request_params["timeInForce"] = CONSTANTS.TimeInForce.GTC
            else:
                request_params["expiration"] = expiration
        response = await self._api_post(path_url=order_url, data=request_params, is_auth_required=True)
        order_id = response["id"]
        order_time = response["createdAt"] / 1000
        return order_id, order_time

    async def _place_order_build_order(
        self,
        exchange_symbol: str,
        side: str,
        order_type: str,
        amount: Decimal,
        price: Decimal,
        time_in_force: CONSTANTS.TimeInForce = CONSTANTS.TimeInForce.GTC,
        expiration: Optional[int] = None,
    ):
        full_url = web_utils.private_rest_url(CONSTANTS.ORDER_BUILD_URL, domain=self.name)
        request_params = {
            "marketId": exchange_symbol,
            "side": side,
            "orderType": order_type,
            "amount": amount,
            "price": price,
            "timeInForce": time_in_force.value,
        }
        if time_in_force == CONSTANTS.TimeInForce.GTT:
            if expiration is None:
                request_params["timeInForce"] = CONSTANTS.TimeInForce.GTC
            else:
                request_params["expiration"] = expiration
        response = await self._api_post(path_url=full_url, data=request_params, is_auth_required=True)
        """
        {'gasFeeQuotation': 'some hash',
         'order': {'creditAmount': '-40000000',
                   'info': '0xhash',
                   'paperAmount': '20000000000000000',
                   'perp': '0xhash',
                   'sender': '0x0',
                   'singer': 'wallet address'},
         'orderHash': 'some hash',
         'packedOrder': 'some hash',
         }
        """
        return response

    async def _place_cancel(self, order_id: str, tracked_order: InFlightOrder):
        cancel_url = web_utils.private_rest_url(CONSTANTS.ORDER_URL, domain=self.name)
        exchange_symbol = await self.exchange_symbol_associated_to_pair(tracked_order.trading_pair)
        request_params = {"orderId": order_id, "marketId": exchange_symbol}
        response_msg = await self._api_delete(path_url=cancel_url, data=request_params, is_auth_required=True)
        if response_msg:
            self.logger().error(f"Cancel order failed: {response_msg = }")
            raise CONSTANTS.JojoOrderNotFoundError(f"Cancel order failed: {response_msg = }")

    async def _set_trading_pair_leverage(self, trading_pair: str, leverage: int) -> Tuple[bool, str]:
        return True, ""

    async def _trading_pair_position_mode_set(self, mode: PositionMode, trading_pair: str) -> Tuple[bool, str]:
        return True, ""

    async def _fetch_last_fee_payment(self, trading_pair: str) -> Tuple[float, Decimal, Decimal]:
        # return timestamp, funding_rate, payment
        funding_info: Optional[FundingInfo] = self._orderbook_ds.get_latest_funding_info(trading_pair)  # type: ignore
        funding_fee: Optional[Dict[str, Any]] = self._raw_funding_fees_websocket.get(trading_pair)
        if funding_info is None or funding_fee is None:
            return 0, Decimal("-1"), Decimal("-1")
        funding_time = funding_fee["time"] / 1000
        payment = Decimal(funding_fee["amount"])
        return funding_time, funding_info.rate, payment

    async def _request_order_status(self, tracked_order: InFlightOrder) -> OrderUpdate:
        open_order_url = web_utils.private_rest_url(CONSTANTS.OPEN_ORDER_URL, domain=self.name)
        exchange_symbol = await self.exchange_symbol_associated_to_pair(tracked_order.trading_pair)
        request_params = {"orderId": tracked_order.exchange_order_id, "marketId": exchange_symbol}
        response = await self._api_get(path_url=open_order_url, params=request_params, is_auth_required=True)
        if "code" in response:
            # error
            self.logger().error(f"Error fetching order status: {response = }")
            raise CONSTANTS.JojoOrderNotFoundError(
                f"No order={tracked_order.exchange_order_id} in _request_order_status: {response = }"
            )
        else:
            return OrderUpdate(
                trading_pair=tracked_order.trading_pair,
                update_timestamp=self._time_synchronizer.time(),
                new_state=CONSTANTS.ORDER_STATUS[response["status"]],
                client_order_id=tracked_order.client_order_id,
                exchange_order_id=tracked_order.exchange_order_id,
            )

    async def _all_trade_updates_for_order(self, order: InFlightOrder) -> List[TradeUpdate]:
        trades_url = web_utils.private_rest_url(CONSTANTS.USER_TRADES_URL, domain=self.name)
        exchange_symbol = await self.exchange_symbol_associated_to_pair(order.trading_pair)
        request_params = {"fromId": order.exchange_order_id, "marketId": exchange_symbol}
        response = await self._api_get(path_url=trades_url, params=request_params, is_auth_required=True)
        if "code" in response:
            self.logger().error(f"Error fetching trade updates: {response = }")
            return []

        trade_updates = []
        for trade in response:
            """
            {
                "id": 23,
                "commission": "-0.119924",
                "isMaker": false,
                "isBuyer": false,
                "marketId": "btcusdc",
                "price": "29981",
                "amount": "0.008",
                "quoteAmount": "239.848",
                "time": 1656125389579,
                "status": "SETTLED",
                "timeInForce": "GTC",
                "realizedPNL": "0",
                "orderType": "LIMIT"
            }
            """
            if trade["status"] == "SETTLED":
                trading_fee = self.get_fee(
                    base_currency=order.base_asset,
                    quote_currency=order.quote_asset,
                    order_type=order.order_type,
                    order_side=order.trade_type,
                    position_action=PositionAction.NIL,
                    amount=Decimal(trade["amount"]),
                    price=Decimal(trade["price"]),
                    is_maker=trade["isMaker"],
                )
                trade_update = TradeUpdate(
                    trade_id=trade["id"],
                    client_order_id=order.client_order_id,
                    exchange_order_id=order.exchange_order_id,
                    trading_pair=order.trading_pair,
                    fill_timestamp=trade["time"] / 1000,
                    fill_price=Decimal(trade["price"]),
                    fill_base_amount=Decimal(trade["amount"]),
                    fill_quote_amount=Decimal(trade["quoteAmount"]),
                    fee=trading_fee,
                )
                trade_updates.append(trade_update)
        return trade_updates

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
        is_maker = True if is_maker else False
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
            if "event" in event_message:
                if event_message["event"] == "ACCOUNT_UPDATE":
                    self._raw_balances_websocket = event_message["balances"]
                    self._raw_positions_websocket = event_message["positions"]

                elif event_message["event"] == "INCOME_UPDATE":
                    async with self._mapping_initialization_lock:
                        incomes = event_message["incomes"]
                        for income in incomes:
                            trading_pair = await self.trading_pair_associated_to_exchange_symbol(income["marketId"])
                            if income["type"] == "FUNDING_FEE":
                                old_funding_fee = self._raw_funding_fees_websocket.get(trading_pair, None)
                                if old_funding_fee["time"] < income["time"] or old_funding_fee is None:
                                    """
                                    income = {
                                        "id": 1289,
                                        "type": "FUNDING_FEE",
                                        "amount": "-17.032035",
                                        "time": 1656000030678,
                                        "marketId": "btcusdc"
                                    }
                                    """
                                    self._raw_funding_fees_websocket[trading_pair] = income

                elif event_message["event"] == "ORDER_UPDATE":
                    timestamp = event_message["timestamp"] / 1000
                    order_info = event_message["order"]
                    client_order_id = f"{order_info['marketId']}-{order_info['side']}-{order_info['price']}"
                    trading_pair = await self.trading_pair_associated_to_exchange_symbol(order_info["marketId"])
                    tracked_order: Optional[InFlightOrder] = self._order_tracker.all_fillable_orders.get(
                        client_order_id
                    )
                    if tracked_order is None:
                        self.start_tracking_order(
                            order_id=client_order_id,
                            exchange_order_id=order_info["id"],
                            trading_pair=trading_pair,
                            trade_type=TradeType.BUY if order_info["side"] == "BUY" else TradeType.SELL,
                            price=Decimal(order_info["price"]),
                            amount=Decimal(order_info["amount"]),
                            order_type=OrderType.LIMIT if order_info["type"] == "LIMIT" else OrderType.MARKET,
                        )
                    else:
                        order_status: OrderState = CONSTANTS.ORDER_STATUS[order_info["status"]]
                        order_update = OrderUpdate(
                            trading_pair=tracked_order.trading_pair,
                            update_timestamp=timestamp,
                            new_state=CONSTANTS.ORDER_STATUS[order_info["status"]],
                            client_order_id=client_order_id,
                            exchange_order_id=order_info["id"],
                        )
                        self._order_tracker.process_order_update(order_update)
                        if order_status in [OrderState.FILLED, OrderState.CANCELED, OrderState.FAILED]:
                            self.stop_tracking_order(client_order_id)

                elif event_message["event"] == "TRADE_UPDATE":
                    # trade_info = event_message["trade"]
                    # filled_time = trade_info["time"] / 1000
                    # trading_pair = await self.trading_pair_associated_to_exchange_symbol(trade_info["marketId"])
                    # side = "BUY" if trade_info["isBuyer"] else "SELL"
                    # order_type = OrderType.LIMIT if trade_info["orderType"] == "LIMIT" else OrderType.MARKET
                    # client_order_id = f"{trade_info['marketId']}-{side}-{trade_info['price']}"
                    # tracked_order: InFlightOrder = self._order_tracker.all_orders[client_order_id]
                    # base_asset, quote_asset = split_hb_trading_pair(trading_pair)
                    # amount = Decimal(trade_info["amount"])
                    # price = Decimal(trade_info["price"])
                    # trade_fee = self.get_fee(
                    #     base_currency=base_asset,
                    #     quote_currency=quote_asset,
                    #     order_type=order_type,
                    #     order_side=TradeType.BUY if side == "BUY" else TradeType.SELL,
                    #     position_action=PositionAction.NIL,
                    #     amount=amount,
                    #     price=price,
                    #     is_maker=trade_info["isMaker"],
                    # )
                    # trade_update: TradeUpdate = TradeUpdate(
                    #     trade_id=trade_info["id"],
                    #     client_order_id=client_order_id,
                    #     exchange_order_id=tracked_order.exchange_order_id,
                    #     trading_pair=trading_pair,
                    #     fill_timestamp=filled_time,
                    #     fill_price=price,
                    #     fill_base_amount=amount,
                    #     fill_quote_amount=Decimal(trade_info["quoteAmount"]),
                    #     fee=trade_fee,
                    #     is_taker=not trade_info["isMaker"],
                    # )
                    # self._order_tracker.process_trade_update(trade_update)

                    pass

                elif event_message["event"] == "DEGEN_ACCOUNT_STATE_UPDATE":
                    pass
                else:
                    self.logger().warning(f"Unrecognized user stream event: {event_message = }")
            else:
                return

    async def _update_balances(self):
        self._account_balances[CONSTANTS.CURRENCY] = Decimal(self._raw_balances_websocket["netValue"])
        self._account_available_balances[CONSTANTS.CURRENCY] = Decimal(self._raw_balances_websocket["availableMargin"])

    async def _update_positions(self):
        async with self._mapping_initialization_lock:
            leverage = Decimal(self._raw_balances_websocket["leverage"])
            for p_info in self._raw_positions_websocket:
                trading_pair = await self.trading_pair_associated_to_exchange_symbol(p_info["symbol"])
                position_side = PositionSide.LONG if p_info["side"] == "LONG" else PositionSide.SHORT
                pos_key = self._perpetual_trading.position_key(trading_pair, position_side)
                if p_info["status"] == "OPEN":
                    unrealized_pnl = Decimal(p_info["unrealizedPnl"])
                    entry_price = Decimal(p_info["entryPrice"])
                    amount = Decimal(p_info["size"])
                    _position = Position(
                        trading_pair=pos_key,
                        position_side=position_side,
                        unrealized_pnl=unrealized_pnl,
                        entry_price=entry_price,
                        amount=amount,
                        leverage=leverage,
                    )
                    self._perpetual_trading.set_position(pos_key, _position)
                else:
                    self._perpetual_trading.remove_position(pos_key)

    async def _format_trading_rules(self, exchange_info_dict: Dict[str, Any]) -> List[TradingRule]:
        raw_info = exchange_info_dict["markets"]
        trading_rules = []
        for info in raw_info:
            trading_pair = await self.trading_pair_associated_to_exchange_symbol(info["symbol"])
            filters = {v["filterType"]: v for v in info["filters"]}
            trading_rule = TradingRule(
                trading_pair,
                min_price_increment=Decimal(filters["PRICE_FILTER"]["tickSize"]),
                min_base_amount_increment=Decimal(filters["AMOUNT_FILTER"]["minAmount"]),
                buy_order_collateral_token=info["baseAssetName"],
                sell_order_collateral_token=info["baseAssetName"],
            )
            trading_rules.append(trading_rule)
        return trading_rules

    def get_buy_collateral_token(self, trading_pair: str) -> str:
        trading_rule: TradingRule = self._trading_rules[trading_pair]
        return trading_rule.buy_order_collateral_token

    def get_sell_collateral_token(self, trading_pair: str) -> str:
        trading_rule: TradingRule = self._trading_rules[trading_pair]
        return trading_rule.sell_order_collateral_token
