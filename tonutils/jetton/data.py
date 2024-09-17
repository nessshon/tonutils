from __future__ import annotations

from typing import Union, Optional

from pytoniq_core import Address, Cell, Slice, TlbScheme, begin_cell

from .content import JettonOnchainContent, JettonOffchainContent


class JettonMasterData(TlbScheme):

    def __init__(
            self,
            admin_address: Optional[Union[Address, str]] = None,
            content: Optional[Union[JettonOffchainContent, JettonOnchainContent, Cell]] = None,
            jetton_wallet_code: Optional[Union[Cell, str]] = None,
            total_supply: Optional[int] = 0,
            mintable: Optional[bool] = True,
    ) -> None:
        self.total_supply = total_supply
        self.mintable = mintable
        if isinstance(admin_address, str):
            admin_address = Address(admin_address)
        self.admin_address = admin_address

        if isinstance(content, (JettonOffchainContent, JettonOnchainContent)):
            content = content.serialize()
        self.content = content

        if isinstance(jetton_wallet_code, str):
            jetton_wallet_code = Cell.one_from_boc(jetton_wallet_code)
        self.jetton_wallet_code = jetton_wallet_code

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_coins(self.total_supply)
            .store_address(self.admin_address)
            .store_ref(self.content)
            .store_ref(self.jetton_wallet_code)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> JettonMasterData:
        raise NotImplementedError


class JettonWalletData(TlbScheme):

    def __init__(
            self,
            owner_address: Optional[Union[Address, str]] = None,
            jetton_master_address: Optional[Union[Address, str]] = None,
            jetton_wallet_code: Optional[Union[Cell, str]] = None,
            balance: int = 0,
    ) -> None:
        if isinstance(owner_address, str):
            owner_address = Address(owner_address)

        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(jetton_wallet_code, str):
            jetton_wallet_code = Cell.one_from_boc(jetton_wallet_code)

        self.owner_address = owner_address
        self.jetton_master_address = jetton_master_address
        self.jetton_wallet_code = jetton_wallet_code
        self.balance = balance

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_coins(self.balance)
            .store_address(self.owner_address)
            .store_address(self.jetton_master_address)
            .store_ref(self.jetton_wallet_code)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> JettonWalletData:
        raise NotImplementedError
