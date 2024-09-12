from typing import Any, Optional, Union

from pytoniq_core import Address, Cell, begin_cell

from tonutils.contract import Contract
from tonutils.vanity.data import VanityData


class Vanity(Contract):
    CODE_HEX = "b5ee9c72010102010032000114ff00f4a413f4bcf2c80b010046d3ed44d075d721fa408307d721d102d0d30331fa403058c705f288d4d4d101fb04ed54"  # noqa

    def __init__(
            self,
            owner_address: Optional[Union[Address, str]] = None,
            salt: Optional[str] = None,
    ) -> None:
        self._data = self.create_data(owner_address, salt).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            owner_address: Optional[Union[Address, str]] = None,
            salt: Optional[str] = None,
    ) -> Any:
        return VanityData(owner_address, salt)

    @classmethod
    def build_deploy_body(cls, contract: Contract) -> Cell:
        return (
            begin_cell()
            .store_ref(contract.code)
            .store_ref(contract.data)
            .end_cell()
        )
