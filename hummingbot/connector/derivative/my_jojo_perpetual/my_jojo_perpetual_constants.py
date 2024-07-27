from enum import Enum

from hummingbot.core.api_throttler.data_types import LinkedLimitWeightPair, RateLimit
from hummingbot.core.data_type.in_flight_order import OrderState

EXCHANGE_NAME = "my_jojo_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = None

CURRENCY = "USDC"


ORDER_STATUS = {
    "CREATED": OrderState.PENDING_CREATE,
    "NEW": OrderState.CREATED,
    "FILLED": OrderState.FILLED,
    "FAILED": OrderState.FAILED,
    "CANCELED": OrderState.CANCELED,
    "EXPIRED": OrderState.CANCELED,
    "PARTIAL_FILLED": OrderState.PARTIALLY_FILLED,
}


class TimeInForce(Enum):
    GTC = "GTC"  # Good till cancelled
    FOK = "FOK"  # Fill or kill
    IOC = "IOC"  # Immediate or cancel
    GTT = "GTT"  # Good till time
    POST_ONLY = "POST_ONLY"


class JojoOrderNotFoundError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


DOMAIN = "my_jojo_perpetual"
TESTNET_DOMAIN = "my_jojo_perpetual_testnet"

API_VERSION = "v1"

HEARTBEAT_TIME_INTERVAL = 15

# public http api
SERVER_TIME_PATH_URL = f"/{API_VERSION}/time"
EXCHANGE_INFO_URL = f"/{API_VERSION}/exchangeInfo"
ORDERBOOK_URL = f"/{API_VERSION}/orderbook"
TRADES_URL = f"/{API_VERSION}/trades"
KLINES_URL = f"/{API_VERSION}/klines"
# MARK_PRICE_KLINES_URL = f"{API_VERSION}/markPriceKlines"
FUNDING_RATE_URL = f"/{API_VERSION}/fundingRate"
# private http api
ACCOUNT_URL = f"/{API_VERSION}/account"
ORDER_BUILD_URL = f"/{API_VERSION}/order/build"
ORDER_URL = f"/{API_VERSION}/order"
ORDER_CANCEL_ALL_URL = f"/{API_VERSION}/allOpenOrders"
OPEN_ORDER_URL = f"/{API_VERSION}/openOrder"
ALL_OPEN_ORDER_URL = f"/{API_VERSION}/OpenOrders"
USER_TRADES_URL = f"/{API_VERSION}/userTrades"
INCOMES_URL = f"/{API_VERSION}/incomes"
BALANCES_URL = f"/{API_VERSION}/balances"
POSITIONS_URL = f"/{API_VERSION}/positions"

# websocket api
WS_SINGLE_URL = f"/{API_VERSION}/single"
WS_COMBINED_URL = f"/{API_VERSION}/multiple"

PERPETUAL_BASE_URL = "https://api.base-mainnet.jojo.exchange"
TESTNET_BASE_URL = "https://api.base-sepolia.jojo.exchange"
PERPETUAL_WS_URL = "wss://stream.base-mainnet.jojo.exchange"
TESTNET_WS_URL = "wss://stream.base-sepolia.jojo.exchange"

COMMON_LIMIT = 2400
ORDER_LIMIT = 1200
TIME_INTERVAL = 60


RATE_LIMITS = [
    RateLimit(limit_id="ALL", limit=COMMON_LIMIT, time_interval=TIME_INTERVAL),
    # common limit
    RateLimit(
        limit_id=SERVER_TIME_PATH_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(SERVER_TIME_PATH_URL)],
    ),
    RateLimit(
        limit_id=EXCHANGE_INFO_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(EXCHANGE_INFO_URL)],
    ),
    RateLimit(
        limit_id=ORDERBOOK_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(ORDERBOOK_URL)],
    ),
    RateLimit(
        limit_id=TRADES_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(TRADES_URL)],
    ),
    RateLimit(
        limit_id=KLINES_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(KLINES_URL)],
    ),
    RateLimit(
        limit_id=FUNDING_RATE_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(FUNDING_RATE_URL)],
    ),
    RateLimit(
        limit_id=ACCOUNT_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(ACCOUNT_URL)],
    ),
    RateLimit(
        limit_id=OPEN_ORDER_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(OPEN_ORDER_URL)],
    ),
    RateLimit(
        limit_id=ALL_OPEN_ORDER_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(ALL_OPEN_ORDER_URL)],
    ),
    RateLimit(
        limit_id=USER_TRADES_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(USER_TRADES_URL)],
    ),
    RateLimit(
        limit_id=INCOMES_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(INCOMES_URL)],
    ),
    RateLimit(
        limit_id=BALANCES_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(BALANCES_URL)],
    ),
    RateLimit(
        limit_id=POSITIONS_URL,
        limit=COMMON_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(POSITIONS_URL)],
    ),
    # order limit
    RateLimit(
        limit_id=ORDER_BUILD_URL,
        limit=ORDER_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(ORDER_BUILD_URL)],
    ),
    RateLimit(
        limit_id=ORDER_URL,
        limit=ORDER_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(ORDER_URL)],
    ),
    RateLimit(
        limit_id=ORDER_CANCEL_ALL_URL,
        limit=ORDER_LIMIT,
        time_interval=TIME_INTERVAL,
        linked_limits=[LinkedLimitWeightPair(ORDER_CANCEL_ALL_URL)],
    ),
]
