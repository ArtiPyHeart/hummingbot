import logging
from decimal import Decimal
from typing import Dict

from pydantic import Field

from hummingbot.client.config.config_data_types import BaseClientModel, ClientFieldData
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.data_type.common import OrderType, PriceType, TradeType
from hummingbot.core.data_type.order_candidate import OrderCandidate
from hummingbot.core.event.events import OrderFilledEvent
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class AvellanedaMarketMakingSpotConfig(BaseClientModel):
    exchange: str = Field("binance_paper_trade", client_data=ClientFieldData(
        prompt=lambda mi: "交易所名称"))
    trading_pair: str = Field("ETH-USDT", client_data=ClientFieldData(
        prompt=lambda mi: "交易对"))
    order_amount: Decimal = Field(0.1, client_data=ClientFieldData(
        prompt=lambda mi: "订单数量"))
    order_refresh_time: int = Field(30, client_data=ClientFieldData(
        prompt=lambda mi: "订单刷新时间(秒)"))
    risk_factor: Decimal = Field(1, client_data=ClientFieldData(
        prompt=lambda mi: "风险因子(γ)"))
    inventory_target_base_pct: Decimal = Field(50, client_data=ClientFieldData(
        prompt=lambda mi: "目标库存百分比"))
    volatility_adjustment_multiplier: Decimal = Field(1, client_data=ClientFieldData(
        prompt=lambda mi: "波动率调整乘数"))


class AvellanedaMarketMakingSpot(ScriptStrategyBase):
    """
    Avellaneda-Stoikov做市策略(无限时间跨度版本)
    """

    def __init__(self, connectors: Dict[str, ConnectorBase], config: AvellanedaMarketMakingSpotConfig):
        super().__init__(connectors)
        self.config = config
        self.create_timestamp = 0
        self.ready_to_trade = False
        self.avg_vol = None
        self.reservation_price = Decimal("0")
        self.optimal_spread = Decimal("0")
        self.optimal_ask = Decimal("0")
        self.optimal_bid = Decimal("0")

    def on_tick(self):
        if not self.ready_to_trade:
            self.ready_to_trade = self.all_assets_ready()
            if not self.ready_to_trade:
                self.logger().warning("等待资产就绪...")
                return

        if self.create_timestamp <= self.current_timestamp:
            self.cancel_all_orders()
            self.calculate_reservation_price_and_optimal_spread()
            proposal = self.create_proposal()
            proposal_adjusted = self.adjust_proposal_to_budget(proposal)
            self.place_orders(proposal_adjusted)
            self.create_timestamp = self.current_timestamp + self.config.order_refresh_time

    def all_assets_ready(self):
        return all(market.ready for market in self.connectors.values())

    def calculate_reservation_price_and_optimal_spread(self):
        market = self.connectors[self.config.exchange]
        mid_price = market.get_price_by_type(self.config.trading_pair, PriceType.MidPrice)
        
        # 计算库存偏差
        base_balance = market.get_available_balance(self.config.trading_pair.split("-")[0])
        quote_balance = market.get_available_balance(self.config.trading_pair.split("-")[1])
        inventory = base_balance + quote_balance / mid_price
        inventory_target = inventory * (self.config.inventory_target_base_pct / Decimal("100"))
        q = (base_balance - inventory_target) / inventory

        # 计算波动率
        if self.avg_vol is None:
            self.avg_vol = market.get_price_by_type(self.config.trading_pair, PriceType.LastTrade)
        else:
            self.avg_vol = Decimal("0.95") * self.avg_vol + Decimal("0.05") * market.get_price_by_type(self.config.trading_pair, PriceType.LastTrade)
        vol = abs(self.avg_vol - mid_price) / mid_price * self.config.volatility_adjustment_multiplier

        # 计算预留价格和最优价差
        self.reservation_price = mid_price - q * self.config.risk_factor * vol
        self.optimal_spread = self.config.risk_factor * vol * Decimal("2")

        self.optimal_ask = self.reservation_price + self.optimal_spread / Decimal("2")
        self.optimal_bid = self.reservation_price - self.optimal_spread / Decimal("2")

    def create_proposal(self) -> list[OrderCandidate]:
        buy_order = OrderCandidate(
            trading_pair=self.config.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=TradeType.BUY,
            amount=self.config.order_amount,
            price=self.optimal_bid
        )
        sell_order = OrderCandidate(
            trading_pair=self.config.trading_pair,
            is_maker=True,
            order_type=OrderType.LIMIT,
            order_side=TradeType.SELL,
            amount=self.config.order_amount,
            price=self.optimal_ask
        )
        return [buy_order, sell_order]

    def adjust_proposal_to_budget(self, proposal: list[OrderCandidate]) -> list[OrderCandidate]:
        return self.connectors[self.config.exchange].budget_checker.adjust_candidates(proposal, all_or_none=True)

    def place_orders(self, proposal: list[OrderCandidate]) -> None:
        for order in proposal:
            self.place_order(self.config.exchange, order)

    def place_order(self, connector_name: str, order: OrderCandidate):
        if order.order_side == TradeType.SELL:
            self.sell(connector_name=connector_name, trading_pair=order.trading_pair,
                      amount=order.amount, order_type=order.order_type, price=order.price)
        elif order.order_side == TradeType.BUY:
            self.buy(connector_name=connector_name, trading_pair=order.trading_pair,
                     amount=order.amount, order_type=order.order_type, price=order.price)

    def cancel_all_orders(self):
        for order in self.get_active_orders(connector_name=self.config.exchange):
            self.cancel(self.config.exchange, order.trading_pair, order.client_order_id)

    def did_fill_order(self, event: OrderFilledEvent):
        msg = (f"{event.trade_type.name} {round(event.amount, 2)} {event.trading_pair} "
               f"{self.config.exchange} at {round(event.price, 2)}")
        self.log_with_clock(logging.INFO, msg)
        self.notify_hb_app_with_timestamp(msg)
