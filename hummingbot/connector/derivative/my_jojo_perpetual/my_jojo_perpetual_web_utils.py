from functools import partial
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS
from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.connector.utils import TimeSynchronizerRESTPreProcessor
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from hummingbot.core.api_throttler.async_throttler_base import AsyncThrottlerBase
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.connections_factory import ConnectionsFactory
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, RESTResponse
from hummingbot.core.web_assistant.connections.rest_connection import RESTConnection
from hummingbot.core.web_assistant.rest_assistant import RESTAssistant
from hummingbot.core.web_assistant.rest_post_processors import RESTPostProcessorBase
from hummingbot.core.web_assistant.rest_pre_processors import RESTPreProcessorBase
from hummingbot.core.web_assistant.web_assistants_factory import WebAssistantsFactory
from hummingbot.core.web_assistant.ws_post_processors import WSPostProcessorBase
from hummingbot.core.web_assistant.ws_pre_processors import WSPreProcessorBase


class MyJojoPerpetualRESTPreProcessor(RESTPreProcessorBase):

    async def pre_process(self, request: RESTRequest) -> RESTRequest:
        if request.method == RESTMethod.POST or request.method == RESTMethod.PUT:
            request.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        return request


class MyJojoPerpetualRESTPostProcessor(RESTPostProcessorBase):

    async def post_process(self, response: RESTResponse) -> RESTResponse:
        if response.status < 400:
            pass
        return response


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
    # api_factory = WebAssistantsFactory(throttler=throttler, rest_pre_processors=[])
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


class MyJojoRestConnection(RESTConnection):
    def __init__(self, aiohttp_client_session: aiohttp.ClientSession):
        super().__init__(aiohttp_client_session=aiohttp_client_session)

    async def call(self, request: RESTRequest) -> RESTResponse:
        if request.method == RESTMethod.GET:
            aiohttp_resp = await self._client_session.get(
                url=request.url,
                params=request.params,
                headers=request.headers,
            )
        elif request.method == RESTMethod.POST:
            aiohttp_resp = await self._client_session.post(
                url=request.url,
                data=request.data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        elif request.method == RESTMethod.DELETE:
            aiohttp_resp = await self._client_session.delete(
                url=request.url,
                params=request.params,
                headers=request.headers,
            )
        elif request.method == RESTMethod.PUT:
            aiohttp_resp = await self._client_session.put(
                url=request.url,
                data=request.data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        else:
            raise NotImplementedError

        resp = await self._build_resp(aiohttp_resp)
        return resp


class MyJojoConnectionsFactory(ConnectionsFactory):
    def __init__(self):
        super().__init__()

    async def get_rest_connection(self) -> RESTConnection:
        shared_client = await self._get_shared_client()
        connection = MyJojoRestConnection(aiohttp_client_session=shared_client)
        return connection


class MyJojoRESTAssistant(RESTAssistant):
    def __init__(
        self,
        connection: RESTConnection,
        throttler: AsyncThrottlerBase,
        rest_pre_processors: Optional[List[RESTPreProcessorBase]] = None,
        rest_post_processors: Optional[List[RESTPostProcessorBase]] = None,
        auth: Optional[AuthBase] = None,
    ):
        super().__init__(
            connection=connection,
            throttler=throttler,
            rest_pre_processors=rest_pre_processors,
            rest_post_processors=rest_post_processors,
            auth=auth,
        )

    async def execute_request_and_get_response(
        self,
        url: str,
        throttler_limit_id: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        method: RESTMethod = RESTMethod.GET,
        is_auth_required: bool = False,
        return_err: bool = False,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> RESTResponse:

        local_headers = headers or {}

        data = data if data else None

        request = RESTRequest(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=local_headers,
            is_auth_required=is_auth_required,
            throttler_limit_id=throttler_limit_id,
        )

        async with self._throttler.execute_task(limit_id=throttler_limit_id):
            response = await self.call(request=request, timeout=timeout)

            if 400 <= response.status:
                if not return_err:
                    error_response = await response.text()
                    error_text = "N/A" if "<html" in error_response else error_response
                    raise IOError(
                        f"Error executing request {method.name} {url}. HTTP status is {response.status}. "
                        f"Error: {error_text}"
                    )
            return response


class MyJojoWebAssistantsFactory(WebAssistantsFactory):
    def __init__(
        self,
        throttler: AsyncThrottlerBase,
        rest_pre_processors: Optional[List[RESTPreProcessorBase]] = None,
        rest_post_processors: Optional[List[RESTPostProcessorBase]] = None,
        ws_pre_processors: Optional[List[WSPreProcessorBase]] = None,
        ws_post_processors: Optional[List[WSPostProcessorBase]] = None,
        auth: Optional[AuthBase] = None,
    ):
        super().__init__(
            throttler=throttler,
            rest_pre_processors=rest_pre_processors,
            rest_post_processors=rest_post_processors,
            ws_pre_processors=ws_pre_processors,
            ws_post_processors=ws_post_processors,
            auth=auth,
        )
        self._connections_factory = MyJojoConnectionsFactory()

    async def get_rest_assistant(self) -> RESTAssistant:
        connection = await self._connections_factory.get_rest_connection()
        assistant = MyJojoRESTAssistant(
            connection=connection,
            throttler=self._throttler,
            rest_pre_processors=self._rest_pre_processors,
            rest_post_processors=self._rest_post_processors,
            auth=self._auth,
        )
        return assistant


def build_api_factory(
    throttler: Optional[AsyncThrottler] = None,
    time_synchronizer: Optional[TimeSynchronizer] = None,
    domain: str = CONSTANTS.DOMAIN,
    time_provider: Optional[Callable] = None,
    auth: Optional[AuthBase] = None,
) -> WebAssistantsFactory:
    throttler = throttler or create_throttler()
    time_synchronizer = time_synchronizer or TimeSynchronizer()
    time_provider = time_provider or partial(get_current_server_time, throttler=throttler, domain=domain)
    api_factory = MyJojoWebAssistantsFactory(
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
