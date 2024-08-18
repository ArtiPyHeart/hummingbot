import os
from typing import Dict, List

from pydantic import Field, validator

from hummingbot.client.config.config_data_types import ClientFieldData
from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.clock import Clock
from hummingbot.core.data_type.common import PositionMode
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy.strategy_v2_base import StrategyV2Base, StrategyV2ConfigBase
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, StopExecutorAction


class ShowInfoConfig(StrategyV2ConfigBase):
    script_file_name: str = Field(default_factory=lambda: os.path.basename(__file__))
    markets: Dict[str, List[str]] = {}
    candles_config: List[CandlesConfig] = []
    controllers_config: List[str] = []
    exchange: str = Field(
        default="my_jojo_perpetual",
        client_data=ClientFieldData(prompt_on_new=True, prompt=lambda mi: "Exchange where the bot will trade"),
    )
    trading_pair: str = Field(
        default="ETH-USDC",
        client_data=ClientFieldData(prompt_on_new=True, prompt=lambda mi: "Trading pair where the bot will trade"),
    )
    candles_exchange: str = Field(
        default="my_jojo_perpetual",
        client_data=ClientFieldData(prompt_on_new=True, prompt=lambda mi: "Candles exchange"),
    )
    candles_pair: str = Field(
        default="ETH-USDC",
        client_data=ClientFieldData(prompt_on_new=True, prompt=lambda mi: "Candles trading pair"),
    )
    candles_interval: str = Field(
        default="1M",
        client_data=ClientFieldData(prompt_on_new=False, prompt=lambda mi: "Candle interval"),
    )
    candles_length: int = Field(
        default=150,
        gt=0,
        client_data=ClientFieldData(prompt_on_new=True, prompt=lambda mi: "Number of candles"),
    )
    position_mode: PositionMode = Field(
        default="ONEWAY",
        client_data=ClientFieldData(prompt_on_new=True, prompt=lambda mi: "Position mode (HEDGE/ONEWAY)"),
    )

    @validator("position_mode", pre=True, allow_reuse=True)
    def validate_position_mode(cls, v: str) -> PositionMode:
        if v.upper() in PositionMode.__members__:
            return PositionMode[v.upper()]
        raise ValueError(f"Invalid position mode: {v}. Valid options are: {', '.join(PositionMode.__members__)}")


class ShowInfo(StrategyV2Base):
    account_config_set = False

    @classmethod
    def init_markets(cls, config: ShowInfoConfig):
        cls.markets = {config.exchange: {config.trading_pair}}

    def __init__(self, connectors: Dict[str, ConnectorBase], config: ShowInfoConfig):
        if len(config.candles_config) == 0:
            config.candles_config.append(
                CandlesConfig(
                    connector=config.candles_exchange,
                    trading_pair=config.candles_pair,
                    interval=config.candles_interval,
                    max_records=config.candles_length + 1,
                )
            )
        super().__init__(connectors, config)
        self.config = config

    def start(self, clock: Clock, timestamp: float):
        self._last_timestamp = timestamp
        self.apply_initial_setting()

    def create_actions_proposal(self) -> List[CreateExecutorAction]:
        return []

    def stop_actions_proposal(self) -> List[StopExecutorAction]:
        return []

    def apply_initial_setting(self):
        if not self.account_config_set:
            for connector_name, connector in self.connectors.items():
                if self.is_perpetual(connector_name):
                    connector.set_position_mode(self.config.position_mode)
            self.account_config_set = True

    def format_status(self) -> str:
        if not self.ready_to_trade:
            return "Market connectors are not ready."

        lines = []
        warning_lines = []
        warning_lines.extend(self.network_warning(self.get_market_trading_pair_tuples()))

        balance_df = self.get_balance_df()
        lines.extend(["", "  Balances:"] + ["    " + line for line in balance_df.to_string(index=False).split("\n")])
        market_status_df = self._get_market_status_df_with_depth()
        lines.extend(
            ["", "  Market Status Data Frame:"]
            + ["    " + line for line in market_status_df.to_string(index=False).split("\n")]
        )
        candle_df = self.market_data_provider.get_candles_df(
            self.config.candles_exchange,
            self.config.candles_pair,
            self.config.candles_interval,
            self.config.candles_length + 1,
        )
        lines.extend(
            ["", "  Candle Data Frame:"]
            + ["    " + line for line in candle_df.head().to_string(index=False).split("\n")]
        )

        warning_lines.extend(self.balance_warning(self.get_market_trading_pair_tuples()))
        if len(warning_lines) > 0:
            lines.extend(["", "*** WARNINGS ***"] + warning_lines)
        return "\n".join(lines)

    def _get_market_status_df_with_depth(self):
        market_status_df = self.market_status_data_frame(self.get_market_trading_pair_tuples())
        market_status_df["Exchange"] = market_status_df.apply(
            lambda x: x["Exchange"].strip("PaperTrade") + "paper_trade", axis=1
        )
        market_status_df["Volume (+1%)"] = market_status_df.apply(
            lambda x: self._get_volume_for_percentage_from_mid_price(x, 0.01), axis=1
        )
        market_status_df["Volume (-1%)"] = market_status_df.apply(
            lambda x: self._get_volume_for_percentage_from_mid_price(x, -0.01), axis=1
        )
        return market_status_df

    def _get_volume_for_percentage_from_mid_price(self, row, percentage):
        price = row["Mid Price"] * (1 + percentage)
        is_buy = percentage > 0
        result = self.connectors[row["Exchange"]].get_volume_for_price(row["Market"], is_buy, price)
        return result.result_volume
