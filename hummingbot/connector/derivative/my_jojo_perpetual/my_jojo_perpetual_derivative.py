from typing import Optional, List, TYPE_CHECKING

import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.perpetual_derivative_py_base import PerpetualDerivativePyBase
import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_constants as CONSTANTS

if TYPE_CHECKING:
    from hummingbot.client.config.config_helpers import ClientConfigAdapter


class MyJojoPerpetualDerivative(PerpetualDerivativePyBase):
    web_utils = web_utils

    def __init__(
        self,
        client_config_map: "ClientConfigAdapter",
        trading_pairs: Optional[List[str]] = None,
        trading_required: bool = True,
        domain: str = CONSTANTS.DOMAIN,
    ):
        self._trading_pairs = trading_pairs
        self._trading_required = trading_required
        self._domain = domain

        super().__init__(client_config_map=client_config_map)

    async def _get_last_traded_price(self, trading_pair: str) -> float:
        pass
