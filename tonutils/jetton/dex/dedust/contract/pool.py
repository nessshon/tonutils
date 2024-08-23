from enum import Enum
from typing import Union

from pytoniq_core import Address


class PoolType(Enum):
    VOLATILE = 0
    STABLE = 1


class Pool:

    def __init__(
            self,
            address: Union[Address, str]
    ) -> None:
        if isinstance(address, str):
            address = Address(address)

        self.address = address
