from bidict import bidict

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    API_VERSION,
    COMMON_LIMIT,
    TIME_INTERVAL,
)
from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit

REST_URL = "https://api.base-mainnet.jojo.exchange"
HEALTH_CHECK_ENDPOINT = f"/{API_VERSION}/time"
CANDLES_ENDPOINT = f"/{API_VERSION}/klines"

WSS_URL = "wss://stream.base-mainnet.jojo.exchange"

INTERVALS = bidict(
    {
        "1M": 60,
        "5M": 300,
        "15M": 900,
        "30M": 1800,
        "1H": 3600,
        "2H": 7200,
        "4H": 14400,
        "6H": 21600,
        "1D": 86400,
        "1W": 604800,
        "1MO": 2592000,
    }
)

RATE_LIMITS = [
    RateLimit(limit_id="COMMON_LIMIT", limit=COMMON_LIMIT, time_interval=TIME_INTERVAL),
    RateLimit(
        limit_id=CANDLES_ENDPOINT,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair("COMMON_LIMIT")],
    ),
    RateLimit(
        limit_id=HEALTH_CHECK_ENDPOINT,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair("COMMON_LIMIT")],
    ),
]
