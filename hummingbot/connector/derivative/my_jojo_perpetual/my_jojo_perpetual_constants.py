from hummingbot.core.api_throttler.data_types import RateLimit

EXCHANGE_NAME = "my_jojo_perpetual"
BROKER_ID = "HBOT"
MAX_ORDER_ID_LEN = None

DOMAIN = "my_jojo_perpetual"
TESTNET_DOMAIN = "my_jojo_perpetual_testnet"

API_VERSION = "v1"

# public http api
SERVER_TIME_PATH_URL = f"{API_VERSION}/time"
EXCHANGE_INFO_URL = f"{API_VERSION}/exchangeInfo"
ORDER_BOOK_URL = f"{API_VERSION}/orderbook"
TRADES_URL = f"{API_VERSION}/trades"
KLINES_URL = f"{API_VERSION}/klines"
# MARK_PRICE_KLINES_URL = f"{API_VERSION}/markPriceKlines"
FUNDING_RATE_URL = f"{API_VERSION}/fundingRate"
# private http api


PERPETUAL_BASE_URL = "https://api.base-mainnet.jojo.exchange"
TESTNET_BASE_URL = "https://api.base-sepolia.jojo.exchange"
PERPETUAL_WS_URL = "wss://stream.base-mainnet.jojo.exchange"
TESTNET_WS_URL = "wss://stream.base-sepolia.jojo.exchange"

RATE_LIMITS = [
    RateLimit(limit_id="COMMON", limit=2400, time_interval=60),
    RateLimit(limit_id="ORDER", limit=1200, time_interval=60),
]

if __name__ == "__main__":
    from pprint import pprint
    from urllib.parse import urljoin

    import requests

    url = urljoin(PERPETUAL_BASE_URL, FUNDING_RATE_URL)
    response = requests.get(url, params={"marketId": "btcusdc", "limit": 5})
    print(response.status_code)
    pprint(response.json())
