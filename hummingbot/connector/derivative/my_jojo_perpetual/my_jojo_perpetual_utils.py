import time
from decimal import Decimal

from pydantic import Field, SecretStr

from hummingbot.client.config.config_data_types import BaseConnectorConfigMap, ClientFieldData
from hummingbot.core.data_type.trade_fee import TradeFeeSchema

# https://api.base-mainnet.jojo.exchange/v1/exchangeInfo
DEFAULT_FEES = TradeFeeSchema(
    maker_percent_fee_decimal=Decimal("-0.0001"),
    taker_percent_fee_decimal=Decimal("0.0003"),
)

CENTRALIZED = False

EXAMPLE_PAIR = "btcusdc"


def current_time_millis() -> int:
    return int(time.time() * 1000)


def get_expiry_timestamp_in_millis(seconds: int) -> int:
    # must greater than 1 minute and less than 7 day
    seconds = min(max(60, seconds), 604800)
    return current_time_millis() + seconds * 1000


class MyJojoPerpetualConfigMap(BaseConnectorConfigMap):
    connector: str = Field(default="my_jojo_perpetual", client_data=None)
    my_jojo_perpetual_api_secret: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your Base wallet private key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )
    my_jojo_perpetual_api_key: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your Base address",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )

    class Config:
        title = "my_jojo_perpetual"


KEYS = MyJojoPerpetualConfigMap.construct()

OTHER_DOMAINS = ["my_jojo_perpetual_testnet"]
OTHER_DOMAINS_PARAMETER = {"my_jojo_perpetual_testnet": "my_jojo_perpetual_testnet"}
OTHER_DOMAINS_EXAMPLE_PAIR = {"my_jojo_perpetual_testnet": "btcusdc"}
OTHER_DOMAINS_DEFAULT_FEES = {
    "my_jojo_perpetual_testnet": TradeFeeSchema(
        maker_percent_fee_decimal=Decimal("-0.0001"),
        taker_percent_fee_decimal=Decimal("0.0003"),
    )
}


class MyJojoPerpetualTestnetConfigMap(BaseConnectorConfigMap):
    connector: str = Field(default="my_jojo_perpetual_testnet", client_data=None)
    my_jojo_perpetual_api_secret: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your Base wallet private key",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )
    my_jojo_perpetual_api_key: SecretStr = Field(
        default=...,
        client_data=ClientFieldData(
            prompt=lambda cm: "Enter your Base address",
            is_secure=True,
            is_connect_key=True,
            prompt_on_new=True,
        ),
    )

    class Config:
        title = "my_jojo_perpetual_testnet"


OTHER_DOMAINS_KEYS = {"my_jojo_perpetual_testnet": MyJojoPerpetualTestnetConfigMap.construct()}
