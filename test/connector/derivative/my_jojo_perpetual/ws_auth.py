import asyncio
from test.connector.derivative.my_jojo_perpetual.rest_api import PRIVATE_KEY, PUBLIC_KEY

from furl import furl

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils import build_api_factory
from hummingbot.connector.time_synchronizer import TimeSynchronizer
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
    base_url = web_utils.wss_url(CONSTANTS.WS_SINGLE_URL, CONSTANTS.DOMAIN)
    full_url = furl(base_url)
    account = auth._public_key
    full_url /= f"account@{account}"
    timestamp = int(time_sync.time() * 1e3)
    full_url.args["timestamp"] = timestamp
    sign = auth.sign_message(**{"account": account, "timestamp": timestamp})
    full_url.args["signature"] = sign
    await ws_assistant.connect(full_url.url)

    async for ws_response in ws_assistant.iter_messages():
        print(ws_response.data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.250))
    loop.close()
