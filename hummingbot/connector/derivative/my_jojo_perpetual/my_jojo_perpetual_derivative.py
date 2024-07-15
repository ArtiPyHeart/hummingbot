import hummingbot.connector.derivative.my_jojo_perpetual.my_jojo_perpetual_web_utils as web_utils
from hummingbot.connector.perpetual_derivative_py_base import PerpetualDerivativePyBase


class MyJojoPerpetualDerivative(PerpetualDerivativePyBase):
    web_utils = web_utils
