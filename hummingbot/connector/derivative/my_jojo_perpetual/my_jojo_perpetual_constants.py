from enum import Enum

from hummingbot.core.api_throttler.data_types import RateLimit

EXCHANGE_NAME = "my_jojo_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = None

CURRENCY = "USDC"


class OrderStatus(Enum):
    CREATED = "CREATED"
    NEW = "NEW"
    FILLED = "FILLED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    EXPIRED = "EXPIRED"
    PARTIAL_FILLED = "PARTIAL_FILLED"


class TradeTypes(Enum):
    PENDING = "PENDING"
    FAILED = "FAILED"
    SETTLED = "SETTLED"


class TimeInForce(Enum):
    GTC = "GTC"  # Good till cancelled
    FOK = "FOK"  # Fill or kill
    IOC = "IOC"  # Immediate or cancel
    GTT = "GTT"  # Good till time
    POST_ONLY = "POST_ONLY"


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

RATE_LIMITS = [
    RateLimit(limit_id="COMMON", limit=2400, time_interval=60),
    RateLimit(limit_id="ORDER", limit=1200, time_interval=60),
]
