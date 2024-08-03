import asyncio
from test.connector.derivative.my_jojo_perpetual.rest_api import PRIVATE_KEY, PUBLIC_KEY

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils import build_api_factory
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.connections.data_types import WSJSONRequest
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_assistant import WSAssistant

time_sync = TimeSynchronizer()
auth = MyJojoPerpetualAuth(PUBLIC_KEY, PRIVATE_KEY, time_sync)
api_factory: WebAssistantsFactory = build_api_factory(
    time_synchronizer=time_sync,
    auth=auth,
)


async def main():
    ws_assistant: WSAssistant = await api_factory.get_ws_assistant()
    ws_url = web_utils.wss_url(CONSTANTS.WS_COMBINED_URL, CONSTANTS.DOMAIN)

    await ws_assistant.connect(ws_url)

    payload = {
        "id": 1,
        "method": "SUBSCRIBE",
        "params": [],
    }
    exchange_symbol = "ethusdc"
    market_channel = f"{exchange_symbol}@market"
    orderbook_channel = f"{exchange_symbol}@orderbook"
    trade_channel = f"{exchange_symbol}@trade"
    payload["params"].extend([market_channel, orderbook_channel, trade_channel])

    await ws_assistant.send(WSJSONRequest(payload=payload))

    async for ws_response in ws_assistant.iter_messages():
        print(ws_response.data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.250))
    loop.close()
