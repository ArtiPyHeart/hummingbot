import asyncio
import time
from decimal import Decimal
from pprint import pprint
from test.connector.derivative.my_jojo_perpetual.rest_api import PRIVATE_KEY, PUBLIC_KEY
from urllib.parse import urljoin

from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_auth import MyJojoPerpetualAuth
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants import (
    OPEN_ORDER_URL,
    ORDER_BUILD_URL,
    ORDER_URL,
    PERPETUAL_BASE_URL,
    TimeInForce,
)
from hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils import build_api_factory
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.connections.data_types import RESTMethod
from hummingbot.core.web_assistant.rest_assistant import RESTAssistant
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory

time_sync = TimeSynchronizer()
auth = MyJojoPerpetualAuth(PUBLIC_KEY, PRIVATE_KEY, time_sync)
api_factory: WebAssistantsFactory = build_api_factory(
    time_synchronizer=time_sync,
    auth=auth,
)


async def build_order(rest_assistant: RESTAssistant):
    url = urljoin(PERPETUAL_BASE_URL, ORDER_BUILD_URL)
    params = {
        "marketId": "ethusdc",
        "side": "BUY",
        "orderType": "LIMIT",
        "amount": Decimal("0.02"),
        "price": Decimal("2000"),
        "timeInForce": TimeInForce.GTC.value,
    }
    build_info = await rest_assistant.execute_request(
        url,
        ORDER_BUILD_URL,
        data=params,
        method=RESTMethod.POST,
        is_auth_required=True,
        return_err=True,
    )
    pprint(build_info)
    return build_info


async def place_order(rest_assistant: RESTAssistant, build_info):
    order_url = urljoin(PERPETUAL_BASE_URL, ORDER_URL)
    request_params = {
        "marketId": "ethusdc",
        "side": "BUY",
        "orderType": "LIMIT",
        "amount": Decimal("0.02"),
        "price": Decimal("2000"),
        "timeInForce": TimeInForce.GTC.value,
        "orderSignature": auth.sign_order(build_info["orderHash"]),
        "info": build_info["order"]["info"],
        "gasFeeQuotation": build_info["gasFeeQuotation"],
    }
    order_info = await rest_assistant.execute_request(
        order_url,
        ORDER_URL,
        data=request_params,
        method=RESTMethod.POST,
        is_auth_required=True,
        return_err=True,
    )
    pprint(order_info)
    return order_info


async def view_order(rest_assistant: RESTAssistant, order_info):
    view_url = urljoin(PERPETUAL_BASE_URL, OPEN_ORDER_URL)
    view_params = {
        "orderId": order_info["id"],
        "marketId": "ethusdc",
    }
    view_info = await rest_assistant.execute_request(
        view_url,
        OPEN_ORDER_URL,
        params=view_params,
        method=RESTMethod.GET,
        is_auth_required=True,
        return_err=True,
    )
    pprint(view_info)
    return view_info


async def cancel_order(rest_assistant: RESTAssistant, order_info):
    cancel_url = urljoin(PERPETUAL_BASE_URL, ORDER_URL)
    cancel_params = {
        "orderId": order_info["id"],
        "marketId": "ethusdc",
    }
    cancel_info = await rest_assistant.execute_request(
        cancel_url,
        ORDER_URL,
        params=cancel_params,
        method=RESTMethod.DELETE,
        is_auth_required=True,
        return_err=True,
    )
    pprint(cancel_info)
    return cancel_info


async def main():
    rest_assistant: RESTAssistant = await api_factory.get_rest_assistant()

    build_info = await build_order(rest_assistant)
    order_info = await place_order(rest_assistant, build_info)
    time.sleep(15)
    await view_order(rest_assistant, order_info)
    time.sleep(61)
    await cancel_order(rest_assistant, order_info)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(asyncio.sleep(0.250))
    loop.close()
