from typing import Any, Callable, Dict, Optional
from urllib.parse import urljoin

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.connector.utils import TimeSynchronizerRESTPreProcessor
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest
from hummingbot.core.web_assistant.rest_pre_processors import RESTPreProcessorBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory


class MyJojoPerpetualRESTPreProcessor(RESTPreProcessorBase):

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        if request.headers is None:
            request.headers = {}
        # if request.method == RESTMethod.POST or request.method == RESTMethod.PUT:
        #     request.headers["Content-Type"] = "application/x-www-form-urlencoded"
        return request


def public_rest_url(path_url: str, domain: str = "my_jojo_perpetual"):
    base_url = CONSTANTS.PERPETUAL_BASE_URL if domain == "my_jojo_perpetual" else CONSTANTS.TESTNET_BASE_URL
    return urljoin(base_url, path_url)


def private_rest_url(path_url: str, domain: str = "my_jojo_perpetual"):
    base_url = CONSTANTS.PERPETUAL_BASE_URL if domain == "my_jojo_perpetual" else CONSTANTS.TESTNET_BASE_URL
    return urljoin(base_url, path_url)


def wss_url(endpoint: str, domain: str = "my_jojo_perpetual"):
    base_ws_url = CONSTANTS.PERPETUAL_WS_URL if domain == "my_jojo_perpetual" else CONSTANTS.TESTNET_WS_URL
    return urljoin(base_ws_url, endpoint)


def create_throttler() -> AsyncThrottler:
    return AsyncThrottler(CONSTANTS.RATE_LIMITS)


def build_api_factory_without_time_synchronizer_pre_processor(throttler: AsyncThrottler) -> WebAssistantsFactory:
    api_factory = WebAssistantsFactory(throttler=throttler, rest_pre_processors=[MyJojoPerpetualRESTPreProcessor()])
    return api_factory


async def get_current_server_time(
    throttler: Optional[AsyncThrottler] = None,
    domain: str = CONSTANTS.DOMAIN,
) -> float:
    throttler = throttler or create_throttler()
    api_factory = build_api_factory_without_time_synchronizer_pre_processor(throttler=throttler)
    rest_assistant = await api_factory.get_rest_assistant()
    response = await rest_assistant.execute_request(
        url=public_rest_url(path_url=CONSTANTS.SERVER_TIME_PATH_URL, domain=domain),
        method=RESTMethod.GET,
        throttler_limit_id=CONSTANTS.SERVER_TIME_PATH_URL,
    )
    server_time = response["serverTime"]
    return server_time


async def get_exchange_info(domain: str = CONSTANTS.DOMAIN) -> Dict[str, Any]:
    api_factory = build_api_factory()
    rest_assistant = await api_factory.get_rest_assistant()
    response = await rest_assistant.execute_request(
        url=public_rest_url(path_url=CONSTANTS.EXCHANGE_INFO_URL, domain=domain),
        method=RESTMethod.GET,
        throttler_limit_id=CONSTANTS.RATE_LIMITS[0],
    )
    return response


def build_api_factory(
    throttler: Optional[AsyncThrottler] = None,
    time_synchronizer: Optional[TimeSynchronizer] = None,
    domain: str = CONSTANTS.DOMAIN,
    time_provider: Optional[Callable] = None,
    auth: Optional[AuthBase] = None,
) -> WebAssistantsFactory:
    throttler = throttler or create_throttler()
    time_synchronizer = time_synchronizer or TimeSynchronizer()
    time_provider = time_provider or (
        lambda: get_current_server_time(
            throttler=throttler,
            domain=domain,
        )
    )
    api_factory = WebAssistantsFactory(
        throttler=throttler,
        auth=auth,
        rest_pre_processors=[
            TimeSynchronizerRESTPreProcessor(synchronizer=time_synchronizer, time_provider=time_provider),
            MyJojoPerpetualRESTPreProcessor(),
        ],
    )
    return api_factory


def is_exchange_information_valid(rule: Dict[str, Any]) -> bool:
    return True
