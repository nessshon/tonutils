from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pytoniq_core import Cell, begin_cell, Address, Slice

from ..op_codes import *
from .....client import (
    Client,
    TonapiClient,
    ToncenterClient,
    LiteserverClient,
)
from .....exceptions import UnknownClientError
from .....utils import boc_to_base64_string


class PoolType(Enum):
    VOLATILE = 0
    STABLE = 1


class AssetType(Enum):
    NATIVE = 0
    JETTON = 1


class SwapStep:

    def __init__(
            self,
            pool_address: Address,
            limit: int = 0,
            next_step: Optional[SwapStep] = None
    ):
        self.pool_address = pool_address
        self.limit = limit
        self.next_step = next_step


class Asset:

    def __init__(
            self,
            asset_type: AssetType,
            address: Optional[Union[Address, str]] = None,
    ) -> None:
        if isinstance(address, str):
            address = Address(address)

        self.asset_type = asset_type
        self.address = address

    @staticmethod
    def native() -> Asset:
        return Asset(AssetType.NATIVE)

    @staticmethod
    def jetton(minter: Union[Address, str]) -> Asset:
        return Asset(AssetType.JETTON, minter)

    def to_cell(self) -> Cell:
        if self.asset_type == AssetType.NATIVE:
            return (
                begin_cell()
                .store_uint(0, 4)
                .end_cell()
            )

        return (
            begin_cell()
            .store_uint(AssetType.JETTON.value, 4)
            .store_int(self.address.wc, 8)
            .store_bytes(self.address.hash_part)
            .end_cell()
        )


class Factory:

    @classmethod
    async def get_vault_address(
            cls,
            client: Client,
            address: Union[Address, str],
            asset: Asset,
    ) -> Address:
        if isinstance(address, str):
            address = Address(address)

        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=address.to_str(),
                method_name="get_vault_address",
                stack=[asset.to_cell().to_boc().hex()],
            )
            address = Slice.one_from_boc(method_result["stack"][0]["cell"]).load_address()
        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=address.to_str(),
                method_name="get_vault_address",
                stack=[boc_to_base64_string(asset.to_cell().to_boc())],
            )
            address = Slice.one_from_boc(method_result["stack"][0]["value"]).load_address()
        elif isinstance(client, LiteserverClient):
            method_result = await client.run_get_method(
                address=address.to_str(),
                method_name="get_vault_address",
                stack=[asset.to_cell().begin_parse()],
            )
            address = method_result[0].load_address()
        else:
            raise UnknownClientError(client.__class__.__name__)

        return address

    @classmethod
    async def get_pool_address(
            cls,
            client: Client,
            address: Union[Address, str],
            pool_type: PoolType,
            assets: List[Asset],
    ) -> Address:
        if isinstance(address, str):
            address = Address(address)

        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=address.to_str(),
                method_name="get_pool_address",
                stack=[
                    assets[0].to_cell().to_boc().hex(),
                    assets[1].to_cell().to_boc().hex(),
                    pool_type.value,
                ]
            )
            address = Address(method_result["decoded"].get("pool_address"))
        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=address.to_str(),
                method_name="get_pool_address",
                stack=[
                    pool_type.value,
                    boc_to_base64_string(assets[0].to_cell().to_boc()),
                    boc_to_base64_string(assets[1].to_cell().to_boc()),
                ]
            )
            address = Slice.one_from_boc(method_result["stack"][0]["value"]).load_address()
        elif isinstance(client, LiteserverClient):
            method_result = await client.run_get_method(
                address=address.to_str(),
                method_name="get_pool_address",
                stack=[
                    pool_type.value,
                    assets[0].to_cell().begin_parse(),
                    assets[1].to_cell().begin_parse(),
                ]
            )
            address = method_result[0].load_address()
        else:
            raise UnknownClientError(client.__class__.__name__)

        return address

    @classmethod
    def pack_swap_step(cls, swap_step: Union[SwapStep, None] = None) -> Union[Cell, None]:
        if swap_step is None:
            return None

        return (
            begin_cell()
            .store_address(swap_step.pool_address)
            .store_uint(0, 1)
            .store_coins(swap_step.limit)
            .store_maybe_ref(
                cls.pack_swap_step(swap_step.next_step)
                if swap_step.next_step else
                None
            )
            .end_cell()
        )

    @classmethod
    def create_swap_body(
            cls,
            asset_type: AssetType,
            pool_address: Address,
            amount: int = 0,
            limit: int = 0,
            swap_step: Optional[SwapStep] = None,
            deadline: int = 0,
            recipient_address: Optional[Union[Address, str]] = None,
            referral_address: Optional[Union[Address, str]] = None,
            fulfill_payload: Optional[Cell] = None,
            reject_payload: Optional[Cell] = None,
    ) -> Cell:
        swap_params = (
            begin_cell()
            .store_uint(deadline, 32)
            .store_address(recipient_address)
            .store_address(referral_address)
            .store_maybe_ref(fulfill_payload)
            .store_maybe_ref(reject_payload)
            .end_cell()
        )

        if asset_type == AssetType.NATIVE:
            return (
                begin_cell()
                .store_uint(SWAP_NATIVE_OPCODE, 32)
                .store_uint(0, 64)
                .store_coins(amount)
                .store_address(pool_address)
                .store_uint(0, 1)
                .store_coins(limit)
                .store_maybe_ref(cls.pack_swap_step(swap_step))
                .store_ref(swap_params)
                .end_cell()
            )

        return (
            begin_cell()
            .store_uint(SWAP_JETTON_OPCODE, 32)
            .store_address(pool_address)
            .store_uint(0, 1)
            .store_coins(limit)
            .store_maybe_ref(cls.pack_swap_step(swap_step))
            .store_ref(swap_params)
            .end_cell()
        )
