from __future__ import annotations

import time
from enum import Enum
from typing import List, Optional, Union

from pytoniq_core import Address, Cell, begin_cell

from tonutils.cache import async_cache
from tonutils.client import (
    Client,
)
from .constants import *
from ... import JettonMasterStandard, JettonWalletStandard


class PoolType(Enum):
    VOLATILE = 0
    STABLE = 1


class AssetType(Enum):
    NATIVE = 0
    JETTON = 1


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
        if (
            not isinstance(self.address, Address)
            and not self.asset_type == AssetType.NATIVE
        ):
            raise TypeError("JETTON asset must have a valid Address")

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


class Factory:

    def __init__(
            self,
            client: Client,
            factory_address: Optional[Address] = None,
            native_vault_address: Optional[Address] = None,
    ) -> None:
        self.client = client
        self.factory_address = factory_address or Address(
            FactoryAddresses.TESTNET
            if client.is_testnet else
            FactoryAddresses.MAINNET
        )
        self.native_vault_address = native_vault_address or Address(
            NativeVaultAddresses.TESTNET
            if client.is_testnet else
            NativeVaultAddresses.MAINNET
        )
        self.is_testnet = client.is_testnet

    @classmethod
    def default_deadline(cls) -> int:
        return int(time.time()) + TX_DEADLINE

    @async_cache()
    async def get_vault_address(self, factory_address: Address, asset: Asset) -> Address:
        method_result = await self.client.run_get_method(
            address=factory_address.to_str(),
            method_name="get_vault_address",
            stack=[asset.to_cell()],
        )
        return method_result[0]

    @async_cache()
    async def get_pool_address(self, factory_address: Address, pool_type: PoolType, assets: List[Asset]) -> Address:
        method_result = await self.client.run_get_method(
            address=factory_address.to_str(),
            method_name="get_pool_address",
            stack=[
                pool_type.value,
                assets[0].to_cell(),
                assets[1].to_cell(),
            ]
        )
        return method_result[0]

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
    def build_swap_body(
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
                .store_uint(OpCodes.SWAP_NATIVE, 32)
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
            .store_uint(OpCodes.SWAP_JETTON, 32)
            .store_address(pool_address)
            .store_uint(0, 1)
            .store_coins(limit)
            .store_maybe_ref(cls.pack_swap_step(swap_step))
            .store_ref(swap_params)
            .end_cell()
        )

    async def get_swap_jetton_to_jetton_tx_params(
            self,
            recipient_address: Address,
            offer_jetton_address: Address,
            ask_jetton_address: Address,
            offer_amount: int,
            min_ask_amount: int,
            referral_address: Optional[Address] = None,
            fulfill_payload: Optional[Cell] = None,
            reject_payload: Optional[Cell] = None,
            deadline: Optional[int] = None,
            gas_amount: Optional[int] = None,
            forward_gas_amount: Optional[int] = None,
            query_id: int = 0,
            jetton_custom_payload: Optional[Cell] = None,
    ) -> tuple[Address, int, Cell]:
        offer_pool_address = await self.get_pool_address(
            factory_address=self.factory_address,
            pool_type=PoolType.VOLATILE,
            assets=[
                Asset.jetton(offer_jetton_address),
                Asset.native(),
            ],
        )

        ask_pool_address = await self.get_pool_address(
            factory_address=self.factory_address,
            pool_type=PoolType.VOLATILE,
            assets=[
                Asset.native(),
                Asset.jetton(ask_jetton_address),
            ],
        )

        jetton_wallet_address = await JettonMasterStandard.get_wallet_address(
            client=self.client,
            owner_address=recipient_address,
            jetton_master_address=offer_jetton_address,
        )

        forward_payload = self.build_swap_body(
            asset_type=AssetType.JETTON,
            pool_address=offer_pool_address,
            amount=offer_amount,
            limit=min_ask_amount,
            swap_step=SwapStep(ask_pool_address),
            deadline=deadline or self.default_deadline(),
            referral_address=referral_address,
            fulfill_payload=fulfill_payload,
            reject_payload=reject_payload,
        )

        jetton_vault_address = await self.get_vault_address(self.factory_address, Asset.jetton(offer_jetton_address))
        forward_ton_amount = forward_gas_amount or GasConstants.swap_jetton_to_jetton.FORWARD_GAS_AMOUNT

        body = JettonWalletStandard.build_transfer_body(
            recipient_address=jetton_vault_address,
            jetton_amount=offer_amount,
            response_address=recipient_address,
            forward_payload=forward_payload,
            forward_amount=forward_ton_amount,
            custom_payload=jetton_custom_payload,
            query_id=query_id,
        )

        value = gas_amount or GasConstants.swap_jetton_to_jetton.GAS_AMOUNT

        return jetton_wallet_address, value, body

    async def get_swap_jetton_to_ton_tx_params(
            self,
            recipient_address: Address,
            offer_jetton_address: Address,
            offer_amount: int,
            min_ask_amount: int,
            referral_address: Optional[Address] = None,
            fulfill_payload: Optional[Cell] = None,
            reject_payload: Optional[Cell] = None,
            deadline: Optional[int] = None,
            gas_amount: Optional[int] = None,
            forward_gas_amount: Optional[int] = None,
            query_id: int = 0,
            jetton_custom_payload: Optional[Cell] = None,
    ) -> tuple[Address, int, Cell]:
        pool_address = await self.get_pool_address(
            factory_address=self.factory_address,
            pool_type=PoolType.VOLATILE,
            assets=[
                Asset.native(),
                Asset.jetton(offer_jetton_address),
            ],
        )

        jetton_wallet_address = await JettonMasterStandard.get_wallet_address(
            client=self.client,
            owner_address=recipient_address,
            jetton_master_address=offer_jetton_address,
        )

        forward_payload = Factory.build_swap_body(
            asset_type=AssetType.JETTON,
            pool_address=pool_address,
            amount=offer_amount,
            limit=min_ask_amount,
            deadline=deadline or self.default_deadline(),
            recipient_address=recipient_address,
            referral_address=referral_address,
            fulfill_payload=fulfill_payload,
            reject_payload=reject_payload,
        )

        jetton_vault_address = await self.get_vault_address(self.factory_address, Asset.jetton(offer_jetton_address))
        forward_ton_amount = forward_gas_amount or GasConstants.swap_jetton_to_ton.FORWARD_GAS_AMOUNT

        body = JettonWalletStandard.build_transfer_body(
            recipient_address=jetton_vault_address,
            jetton_amount=offer_amount,
            response_address=recipient_address,
            forward_payload=forward_payload,
            forward_amount=forward_ton_amount,
            custom_payload=jetton_custom_payload,
            query_id=query_id,
        )

        value = gas_amount or GasConstants.swap_jetton_to_ton.GAS_AMOUNT

        return jetton_wallet_address, value, body

    async def get_swap_ton_to_jetton_tx_params(
            self,
            recipient_address: Address,
            offer_jetton_address: Address,
            offer_amount: int,
            min_ask_amount: int,
            referral_address: Optional[Address] = None,
            fulfill_payload: Optional[Cell] = None,
            reject_payload: Optional[Cell] = None,
            deadline: Optional[int] = None,
            forward_gas_amount: Optional[int] = None,
    ) -> tuple[Address, int, Cell]:
        pool_address = await self.get_pool_address(
            factory_address=self.factory_address,
            pool_type=PoolType.VOLATILE,
            assets=[
                Asset.native(),
                Asset.jetton(offer_jetton_address),
            ]
        )

        body = self.build_swap_body(
            asset_type=AssetType.NATIVE,
            pool_address=pool_address,
            amount=offer_amount,
            limit=min_ask_amount,
            deadline=deadline or self.default_deadline(),
            recipient_address=recipient_address,
            referral_address=referral_address,
            fulfill_payload=fulfill_payload,
            reject_payload=reject_payload,
        )

        forward_ton_amount = forward_gas_amount or GasConstants.swap_ton_to_jetton.FORWARD_GAS_AMOUNT
        value = offer_amount + forward_ton_amount

        return self.native_vault_address, value, body
