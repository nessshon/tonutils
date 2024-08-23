from __future__ import annotations

from typing import Union, Optional

from pytoniq_core import Address, Cell, begin_cell

from ..op_codes import *


class SwapStep:

    def __init__(
            self,
            pool_address: Address,
            limit: int = 0,
            next_: Optional[SwapStep] = None
    ):
        self.pool_address = pool_address
        self.limit = limit
        self.next_ = next_


class SwapParams:

    def __init__(
            self,
            deadline: int = 0,
            recipient_address: Union[Address, str, None] = None,
            referral_address: Union[Address, str, None] = None,
            fulfill_payload: Union[Cell, None] = None,
            reject_payload: Union[Cell, None] = None
    ):
        self.deadline = deadline
        self.recipient_address = recipient_address
        self.referral_address = referral_address
        self.fulfill_payload = fulfill_payload
        self.reject_payload = reject_payload


class Vault:
    def __init__(
            self,
            address: Union[Address, str],
    ):
        if isinstance(address, str):
            address = Address(address)

        self.address = address

    @staticmethod
    def pack_swap_params(swap_params: Union[SwapParams, None]) -> Cell:
        if swap_params is None:
            return (
                begin_cell()
                .store_uint(0, 32)
                .store_address(None)
                .store_address(None)
                .store_maybe_ref(None)
                .store_maybe_ref(None)
                .end_cell()
            )
        else:
            return (
                begin_cell()
                .store_uint(swap_params.deadline, 32)
                .store_address(swap_params.recipient_address)
                .store_address(swap_params.referral_address)
                .store_maybe_ref(swap_params.fulfill_payload)
                .store_maybe_ref(swap_params.reject_payload)
                .end_cell()
            )

    @staticmethod
    def pack_swap_step(next_: Union[SwapStep, None] = None) -> Union[Cell, None]:
        if next_ is None:
            return None

        return (
            begin_cell()
            .store_address(next_.pool_address)
            .store_uint(0, 1)
            .store_coins(next_.limit)
            .store_maybe_ref(
                Vault.pack_swap_step(next_.next_)
                if next_.next_ else
                None
            )
            .end_cell()
        )


class VaultNative:
    ADDRESS = "EQDa4VOnTYlLvDJ0gZjNYm5PXfSmmtL6Vs6A_CZEtXCNICq_"  # noqa

    def __init__(
            self,
            address: Union[Address, str],
    ):
        if isinstance(address, str):
            address = Address(address)

        self.address = address

    @staticmethod
    def create_swap_payload(
            amount: int,
            pool_address: Address,
            limit: int = 0,
            query_id: int = 0,
            swap_params: Optional[SwapParams] = None,
            next_: Optional[SwapStep] = None
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(SWAP_NATIVE_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_coins(amount)
            .store_address(pool_address)
            .store_uint(0, 1)
            .store_coins(limit)
            .store_maybe_ref(Vault.pack_swap_step(next_))
            .store_ref(Vault.pack_swap_params(swap_params))
            .end_cell()
        )


class VaultJetton:

    def __init__(
            self, address: Union[Address, str]
    ):
        if isinstance(address, str):
            address = Address(address)

        self.address = address

    @staticmethod
    def create_swap_payload(
            pool_address: Address,
            limit: int = 0,
            next_: Union[SwapStep, None] = None,
            swap_params: Union[SwapParams, None] = None
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(SWAP_JETTON_OPCODE, 32)
            .store_address(pool_address)
            .store_uint(0, 1)
            .store_coins(limit)
            .store_maybe_ref(Vault.pack_swap_step(next_))
            .store_ref(Vault.pack_swap_params(swap_params))
            .end_cell()
        )
