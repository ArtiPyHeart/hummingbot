import logging
import traceback
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List

import numpy as np
from pydantic import Field
from scipy.optimize import curve_fit

from hummingbot.client.config.config_data_types import BaseClientModel, ClientFieldData
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.connector.exchange_py_base import ExchangePyBase
from hummingbot.core.data_type.common import OrderType, PriceType, TradeType
from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.core.event.events import OrderFilledEvent
from hummingbot.strategy.__utils__.trailing_indicators.instant_volatility import InstantVolatilityIndicator
from hummingbot.strategy.order_book_asset_price_delegate import OrderBookAssetPriceDelegate
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class NewTradingIntensityIndicator:
    def __init__(
        self, logger, exchange: ExchangePyBase, trading_pair: str, sampling_length: int = 100, debug: bool = False
    ):
        self.logger = logger
        self.debug = debug
        self.exchange = exchange
        self.trading_pair = trading_pair
        self.sampling_length = sampling_length
        self._alpha = Decimal("0")
        self._kappa = Decimal("0")
        self._price_levels: List[Dict[Decimal, Dict[str, float]]] = []

        self._history_bids_df = None
        self._history_asks_df = None

    @property
    def order_book(self) -> OrderBook:
        return self.exchange.get_order_book(self.trading_pair)

    @property
    def alpha_and_kappa(self):
        self.calculate_alpha_kappa()
        return self._alpha, self._kappa

    def update_price_levels(self, order_book_res: Dict[Decimal, Dict[str, float]]):
        self._price_levels.append(order_book_res)
        if len(self._price_levels) > self.sampling_length:
            # fmt: off
            self._price_levels = self._price_levels[-self.sampling_length:]
            # fmt: on

    def is_ready(self):
        if len(self._price_levels) >= self.sampling_length:
            return True
        else:
            return False

    def update(self):
        if self._history_asks_df is not None and self._history_bids_df is not None:
            mid_price = self.exchange.get_price_by_type(self.trading_pair, PriceType.MidPrice)
            bids_df = self._history_bids_df[self._history_bids_df["price"] > mid_price].copy()
            asks_df = self._history_asks_df[self._history_asks_df["price"] < mid_price].copy()
            if not bids_df.empty and not asks_df.empty:
                self.logger.warning("bids_df and asks_df are BOTH NOT empty!")
            if bids_df.empty and asks_df.empty:
                self.logger.warning("bids_df and asks_df are BOTH empty!")

            if not bids_df.empty:
                bids_df["price_level"] = (bids_df["price"] - mid_price).astype(str).apply(Decimal)
                bids_df.set_index("price_level", inplace=True)
                bids_res: Dict[Decimal, Dict[str, float]] = bids_df[["price", "amount"]].to_dict(orient="index")
                self.update_price_levels(bids_res)
            if not asks_df.empty:
                asks_df["price_level"] = (asks_df["price"] - mid_price).astype(str).apply(Decimal)
                asks_df.set_index("price_level", inplace=True)
                asks_res: Dict[Decimal, Dict[str, float]] = asks_df[["price", "amount"]].to_dict(orient="index")
                self.update_price_levels(asks_res)

        # price, amount, update_id
        self._history_bids_df, self._history_asks_df = self.order_book.snapshot

        if self.debug:
            self.logger.info(f"{type(self._history_bids_df) = }")
            self.logger.info(f"{type(self._history_asks_df) = }")

    def calculate_alpha_kappa(self):
        # 拟合指数衰减函数 λ(p) = α * exp(-κ * p)
        if len(self._price_levels) >= 2:

            def exp_func(x, a, b):
                return a * np.exp(-b * x)

            combined = defaultdict(float)
            for level in self._price_levels:
                for price_lv, details in level.items():
                    combined[price_lv] += details["amount"]
            combined_dict = dict(combined)
            sorted_combined = sorted(combined_dict.items(), key=lambda x: x[0], reverse=True)
            sorted_price_levels, sorted_volumes = zip(*sorted_combined)

            price_level_list = np.array(list(sorted_price_levels), dtype=np.float64)
            volume_list = np.array(list(sorted_volumes), dtype=np.float64)

            if self.debug:
                self.logger.info(f"{price_level_list.tolist() = }")
                self.logger.info(f"{volume_list.tolist() = }")

            try:
                popt, _ = curve_fit(
                    exp_func,
                    price_level_list,
                    volume_list,
                    p0=(self._alpha, self._kappa),
                    method="dogbox",
                    bounds=([0, 0], [np.inf, np.inf]),
                )
                self._alpha = Decimal(str(popt[0]))
                self._kappa = Decimal(str(popt[1]))
                if self.debug:
                    self.logger.info(f"alpha: {self._alpha}, kappa: {self._kappa}")
            except RuntimeError:
                self.logger.warning(f"{traceback.format_exc()}")
                # 拟合失败，重置参数
                self._alpha = Decimal("0")
                self._kappa = Decimal("0")
        else:
            self._alpha = Decimal("0")
            self._kappa = Decimal("0")


class AvellanedaMarketMakingSpotConfig(BaseClientModel):
    exchange: str = Field("bybit", client_data=ClientFieldData(prompt=lambda x: "交易所名称"))
    trading_pair: str = Field("ETH-USDT", client_data=ClientFieldData(prompt=lambda x: "交易对"))
    order_amount: Decimal = Field(0.05, client_data=ClientFieldData(prompt=lambda x: "订单数量"))
    order_refresh_time: int = Field(60, client_data=ClientFieldData(prompt=lambda x: "订单刷新时间(秒)"))
    min_spread: Decimal = Field(0, client_data=ClientFieldData(prompt=lambda x: "最小价差"))
    risk_factor: Decimal = Field(1, client_data=ClientFieldData(prompt=lambda x: "风险因子(γ)"))
    inventory_target_base_pct: Decimal = Field(50, client_data=ClientFieldData(prompt=lambda x: "目标库存百分比"))
    eta: Decimal = Field(1, ge=0, le=1, client_data=ClientFieldData(prompt=lambda x: "订单尺寸调整系数"))
    volatility_buffer_size: int = Field(
        100, ge=1, le=10000, client_data=ClientFieldData(prompt=lambda x: "波动率缓冲区大小")
    )
    trading_intensity_buffer_size: int = Field(
        100, ge=1, le=10000, client_data=ClientFieldData(prompt=lambda x: "交易强度缓冲区大小")
    )


class AvellanedaMarketMakingSpot(ScriptStrategyBase):
    """
    尝试在原来Avellaneda-Stoikov现货做市策略的基础上进行复现(无限时间跨度版本)
    """

    @classmethod
    def init_markets(cls, config: AvellanedaMarketMakingSpotConfig):
        cls.markets = {config.exchange: {config.trading_pair}}

    def __init__(self, connectors: Dict[str, ConnectorBase], config: AvellanedaMarketMakingSpotConfig):
        super().__init__(connectors)
        self.config = config
        self.create_timestamp = 0

        self.avg_vol = InstantVolatilityIndicator(sampling_length=self.config.volatility_buffer_size)
        self.price_delegate = OrderBookAssetPriceDelegate(self.current_market, self.config.trading_pair)
        self.trading_intensity: NewTradingIntensityIndicator = NewTradingIntensityIndicator(
            self.logger(),
            exchange=self.current_market,
            trading_pair=self.config.trading_pair,
            sampling_length=self.config.trading_intensity_buffer_size,
            debug=True,
        )
        self.reservation_price = Decimal("0")
        self.optimal_spread = Decimal("0")
        self.optimal_ask = Decimal("0")
        self.optimal_bid = Decimal("0")
        self._alpha = Decimal("0")
        self._kappa = Decimal("0")
        self._q = 0

    @property
    def current_market(self) -> ExchangePyBase:
        return self.connectors[self.config.exchange]

    @property
    def volatility(self):
        return Decimal(str(self.avg_vol.current_value))

    @property
    def current_mid_price(self) -> Decimal:
        return self.current_market.get_price_by_type(self.config.trading_pair, PriceType.MidPrice)

    def on_tick(self):
        if not self.current_market.ready:
            self.logger().warning("交易所未准备好")
            return
        self.update_avg_vol()
        self.trading_intensity.update()
        if self.is_avg_vol_ready() and self.is_trading_intensity_ready():
            if self.create_timestamp <= self.current_timestamp:
                self.cancel_all_orders()
                self._alpha, self._kappa = self.trading_intensity.alpha_and_kappa
                self.calculate_reservation_price_and_optimal_spread()
                proposal = self.create_proposal()
                proposal_adjusted = self.adjust_proposal_to_budget(proposal)
                self.place_orders(proposal_adjusted)
                self.create_timestamp = self.current_timestamp + self.config.order_refresh_time
        else:
            self.logger().warning(f"波动率指标：{self.is_avg_vol_ready()}")
            self.logger().warning(f"交易强度指标：{len(self.trading_intensity._price_levels) = }")

    def is_avg_vol_ready(self) -> bool:
        return self.avg_vol.is_sampling_buffer_full

    def update_avg_vol(self):
        self.avg_vol.add_sample(self.current_mid_price)

    def is_trading_intensity_ready(self) -> bool:
        return self.trading_intensity.is_ready()

    def calculate_reservation_price_and_optimal_spread(self):
        mid_price = self.current_mid_price

        # 计算库存偏差
        base_balance = self.current_market.get_available_balance(self.config.trading_pair.split("-")[0])
        quote_balance = self.current_market.get_available_balance(self.config.trading_pair.split("-")[1])
        total_inventory_in_base = base_balance + quote_balance / mid_price
        inventory_target = total_inventory_in_base * (self.config.inventory_target_base_pct / Decimal("100"))
        self._q = (base_balance - inventory_target) / total_inventory_in_base

        # 计算波动率
        vol = self.volatility

        # 计算预留价格和最优价差
        self.reservation_price = mid_price - self._q * self.config.risk_factor * vol
        self.optimal_spread = self.config.risk_factor * vol
        self.optimal_spread += 2 * Decimal(1 + self.config.risk_factor / self._kappa).ln() / self.config.risk_factor

        self.optimal_ask = self.reservation_price + self.optimal_spread / Decimal("2")
        self.optimal_bid = self.reservation_price - self.optimal_spread / Decimal("2")
        min_spread = mid_price / 100 * self.config.min_spread
        max_limit_bid = mid_price - min_spread / Decimal("2")
        min_limit_ask = mid_price + min_spread / Decimal("2")

        self.optimal_ask = max(self.optimal_ask, min_limit_ask)
        self.optimal_bid = min(self.optimal_bid, max_limit_bid)

    def create_proposal(self) -> list[OrderCandidate]:
        buy_order = OrderCandidate(
            trading_pair=self.config.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=TradeType.BUY,
            amount=self.config.order_amount * Decimal.exp(-self.config.eta * self._q),
            price=self.optimal_bid,
        )
        sell_order = OrderCandidate(
            trading_pair=self.config.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=TradeType.SELL,
            amount=self.config.order_amount * Decimal.exp(self.config.eta * self._q),
            price=self.optimal_ask,
        )
        return [buy_order, sell_order]

    def adjust_proposal_to_budget(self, proposal: list[OrderCandidate]) -> list[OrderCandidate]:
        return self.current_market.budget_checker.adjust_candidates(proposal, all_or_none=True)

    def place_orders(self, proposal: list[OrderCandidate]) -> None:
        for order in proposal:
            self.place_order(self.config.exchange, order)

    def place_order(self, connector_name: str, order: OrderCandidate):
        if order.order_side == TradeType.SELL:
            self.sell(
                connector_name=connector_name,
                trading_pair=order.trading_pair,
                amount=order.amount * Decimal.exp(self.config.eta * self._q),
                order_type=order.order_type,
                price=order.price,
            )
        elif order.order_side == TradeType.BUY:
            self.buy(
                connector_name=connector_name,
                trading_pair=order.trading_pair,
                amount=order.amount * Decimal.exp(-self.config.eta * self._q),
                order_type=order.order_type,
                price=order.price,
            )

    def cancel_all_orders(self):
        for order in self.get_active_orders(connector_name=self.config.exchange):
            self.cancel(self.config.exchange, order.trading_pair, order.client_order_id)

    def did_fill_order(self, event: OrderFilledEvent):
        msg = (
            f"{event.trade_type.name} {round(event.amount, 2)} {event.trading_pair} "
            f"{self.config.exchange} at {round(event.price, 2)}"
        )
        self.log_with_clock(logging.INFO, msg)
        self.notify_hb_app_with_timestamp(msg)
