from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Union, TYPE_CHECKING

from pytoniq_core import Address, Cell, StateInit, WalletMessage, begin_cell

from tonutils.dns.utils import resolve_wallet_address
from tonutils.jetton import JettonMasterStandard, JettonWalletStandard
from tonutils.jetton.dex.dedust import Factory
from tonutils.jetton.dex.stonfi import StonfiRouterV1, StonfiRouterV2
from tonutils.jetton.dex.stonfi.utils import get_stonfi_router_details
from tonutils.nft import NFTStandard
from tonutils.utils import to_nano
from tonutils.wallet.op_codes import TEXT_COMMENT_OPCODE

if TYPE_CHECKING:
    from tonutils.wallet import Wallet


class TransferMessageBase(ABC):

    @abstractmethod
    async def build(self, wallet: Wallet) -> WalletMessage:
        pass


class TransferMessage(TransferMessageBase):
    """
    Data class for transferring funds.

    :param destination: Address object, address string, or a .ton/.t.me domain.
    :param amount: The amount to transfer.
    :param body: The body of the message. Defaults to an empty cell.
        If a string is provided, it will be used as a transaction comment.
    :param state_init: The state init data. Defaults to None.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            destination: Union[Address, str],
            amount: Union[int, float],
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
            **kwargs,
    ) -> None:
        self.destination = destination
        self.amount = amount
        self.body = body
        self.state_init = state_init
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        self.destination = await resolve_wallet_address(wallet.client, self.destination)

        return wallet.create_wallet_internal_message(
            destination=self.destination,
            value=to_nano(self.amount),
            body=self.body,
            state_init=self.state_init,
            **self.other,
        )


class TransferNFTMessage(TransferMessageBase):
    """
    Data class for transferring NFT.

    :param destination: Address object, address string, or a .ton/.t.me domain.
    :param nft_address: The NFT item address.
    :param response_address: The address to receive the notification. Defaults to the destination address.
    :param forward_payload: Optional forward payload.
        If a string is provided, it will be used as a transaction comment.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON. Defaults to 0.000000001.
        A notification will be sent to the new owner if the amount is greater than 0;
    :param amount: The amount to transfer. Defaults to 0.05.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            destination: Union[Address, str],
            nft_address: Union[Address, str],
            response_address: Optional[Union[Address, str]] = None,
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.000000001,
            amount: Union[int, float] = 0.05,
            **kwargs,
    ) -> None:
        if isinstance(nft_address, str):
            nft_address = Address(nft_address)
        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(TEXT_COMMENT_OPCODE, 32)
                .store_snake_string(forward_payload)
                .end_cell()
            )

        self.destination = destination
        self.nft_address = nft_address
        self.response_address = response_address
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.amount = amount
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        self.destination = await resolve_wallet_address(wallet.client, self.destination)

        return wallet.create_wallet_internal_message(
            destination=self.nft_address,
            value=to_nano(self.amount),
            body=NFTStandard.build_transfer_body(
                new_owner_address=self.destination,
                response_address=self.response_address,
                forward_payload=self.forward_payload,
                forward_amount=to_nano(self.forward_amount),

            ),
            **self.other,
        )


class TransferJettonMessage(TransferMessageBase):
    """
    Data class for transferring jettons.

    :param destination: Address object, address string, or a .ton/.t.me domain.
    :param jetton_master_address: The jetton master address.
    :param jetton_amount: The amount of jettons to transfer.
    :param jetton_decimals: The jetton decimals. Defaults to 9.
    :param jetton_wallet_address: Optional jetton wallet address.
    :param forward_payload: Optional forward payload.
        If a string is provided, it will be used as a transaction comment.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON. Defaults to 0.000000001.
        A notification will be sent to the new owner if the amount is greater than 0;
    :param amount: The amount to transfer. Defaults to 0.05.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            destination: Union[Address, str],
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            jetton_wallet_address: Optional[Union[Address, str]] = None,
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.000000001,
            amount: Union[int, float] = 0.05,
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)
        if isinstance(jetton_wallet_address, str):
            jetton_wallet_address = Address(jetton_wallet_address)
        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(TEXT_COMMENT_OPCODE, 32)
                .store_snake_string(forward_payload)
                .end_cell()
            )

        self.destination = destination
        self.jetton_master_address = jetton_master_address
        self.jetton_amount = jetton_amount
        self.jetton_decimals = jetton_decimals
        self.jetton_wallet_address = jetton_wallet_address
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.amount = amount
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        self.destination = await resolve_wallet_address(wallet.client, self.destination)

        if self.jetton_wallet_address is None:
            self.jetton_wallet_address = await JettonMasterStandard.get_wallet_address(
                client=wallet.client,
                owner_address=wallet.address.to_str(),
                jetton_master_address=self.jetton_master_address,
            )

        return wallet.create_wallet_internal_message(
            destination=self.jetton_wallet_address,
            value=to_nano(self.amount),
            body=JettonWalletStandard.build_transfer_body(
                recipient_address=self.destination,
                response_address=wallet.address,
                jetton_amount=int(self.jetton_amount * (10 ** self.jetton_decimals)),
                forward_payload=self.forward_payload,
                forward_amount=to_nano(self.forward_amount),
            ),
            **self.other,
        )


class DedustSwapTONToJettonMessage(TransferMessageBase):
    """
    Data class for swapping TON.

    :param jetton_master_address: The address of the jetton master contract.
    :param ton_amount: The amount of TON to swap.
    :param min_amount: The minimum amount of Jetton to receive. Defaults to 0.
    :param jetton_decimals: Jetton decimal precision used to convert min_amount to nano units.
    :param forward_amount: Forward fee amount. Defaults to 0.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            jetton_master_address: Union[Address, str],
            ton_amount: Union[int, float],
            min_amount: Union[int, float] = 0,
            jetton_decimals: int = 9,
            forward_amount: Union[int, float] = 0,
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)
        if isinstance(factory_address, str):
            factory_address = Address(factory_address)
        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        self.jetton_master_address = jetton_master_address
        self.ton_amount = ton_amount
        self.min_amount = min_amount
        self.jetton_decimals = jetton_decimals
        self.forward_amount = forward_amount
        self.factory_address = factory_address
        self.native_vault_address = native_vault_address
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        factory = Factory(wallet.client, self.factory_address, self.native_vault_address)
        to, value, body = await factory.get_swap_ton_to_jetton_tx_params(
            recipient_address=wallet.address,
            offer_jetton_address=self.jetton_master_address,
            offer_amount=to_nano(self.ton_amount),
            min_ask_amount=to_nano(self.min_amount, self.jetton_decimals),
        )

        return wallet.create_wallet_internal_message(
            destination=to,
            value=value,
            body=body,
            bounce=True,
            **self.other,
        )


class StonfiSwapTONToJettonMessage(TransferMessageBase):
    """
    Data class for swapping TON.

    :param jetton_master_address: The address of the jetton master contract.
    :param ton_amount: The amount of TON to swap.
    :param min_amount: The minimum amount of Jetton to receive. Defaults to 0.
    :param jetton_decimals: Jetton decimal precision used to convert min_amount to nano units.
    :param forward_amount: Forward fee amount. Defaults to 0.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            jetton_master_address: Union[Address, str],
            ton_amount: Union[int, float],
            min_amount: Union[int, float] = 0,
            jetton_decimals: int = 9,
            forward_amount: Union[int, float] = 0,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
            dex_version: Optional[int] = None,
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)
        if isinstance(router_address, str):
            router_address = Address(router_address)
        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        self.jetton_master_address = jetton_master_address
        self.ton_amount = ton_amount
        self.min_amount = min_amount
        self.jetton_decimals = jetton_decimals
        self.forward_amount = forward_amount
        self.router_address = router_address
        self.pton_address = pton_address
        self.dex_version = dex_version
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        if self.dex_version is None and None in (self.router_address, self.pton_address):
            self.dex_version, self.router_address, self.pton_address = await get_stonfi_router_details(
                offer_address="ton",
                ask_address=self.jetton_master_address.to_str(),
                amount=self.ton_amount,
                decimals=9,
                is_testnet=wallet.client.is_testnet,
            )
        if self.dex_version == 1:
            router_v1 = StonfiRouterV1(wallet.client, self.router_address, self.pton_address)
            to, value, body = await router_v1.get_swap_ton_to_jetton_tx_params(
                user_wallet_address=wallet.address,
                ask_jetton_address=self.jetton_master_address,
                offer_amount=to_nano(self.ton_amount),
                min_ask_amount=to_nano(self.min_amount, self.jetton_decimals),
            )
        elif self.dex_version == 2:
            router_v2 = StonfiRouterV2(wallet.client, self.router_address, self.pton_address)
            to, value, body = await router_v2.get_swap_ton_to_jetton_tx_params(
                user_wallet_address=wallet.address,
                receiver_address=wallet.address,
                ask_jetton_address=self.jetton_master_address,
                offer_amount=to_nano(self.ton_amount),
                min_ask_amount=to_nano(self.min_amount, self.jetton_decimals),
                refund_address=wallet.address,
            )
        else:
            raise ValueError(f"Unsupported STONfi Router version: {self.dex_version}")

        return wallet.create_wallet_internal_message(
            destination=to,
            value=value,
            body=body,
            bounce=True,
            **self.other,
        )


class DedustSwapJettonToTONMessage(TransferMessageBase):
    """
    Data class for swapping jettons.

    :param jetton_master_address: The address of the jetton master contract.
    :param jetton_amount: The amount of jettons to swap.
    :param jetton_decimals: The jetton decimals. Defaults to 9.
    :param min_amount: The minimum amount of TON to receive. Defaults to 0.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            min_amount: Union[int, float] = 0,
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)
        if isinstance(factory_address, str):
            factory_address = Address(factory_address)
        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        self.jetton_master_address = jetton_master_address
        self.jetton_amount = jetton_amount
        self.jetton_decimals = jetton_decimals
        self.min_amount = min_amount
        self.factory_address = factory_address
        self.native_vault_address = native_vault_address
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        factory = Factory(wallet.client, self.factory_address, self.native_vault_address)
        to, value, body = await factory.get_swap_jetton_to_ton_tx_params(
            recipient_address=wallet.address,
            offer_jetton_address=self.jetton_master_address,
            offer_amount=to_nano(self.jetton_amount, self.jetton_decimals),
            min_ask_amount=to_nano(self.min_amount),
        )

        return wallet.create_wallet_internal_message(
            destination=to,
            value=value,
            body=body,
            bounce=True,
            **self.other,
        )


class StonfiSwapJettonToTONMessage(TransferMessageBase):
    """
    Data class for swapping jettons.

    :param jetton_master_address: The address of the jetton master contract.
    :param jetton_amount: The amount of jettons to swap.
    :param jetton_decimals: The jetton decimals. Defaults to 9.
    :param min_amount: The minimum amount of TON to receive. Defaults to 0.
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            min_amount: Union[int, float] = 0,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
            dex_version: Optional[int] = None,
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)
        if isinstance(router_address, str):
            router_address = Address(router_address)
        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        self.jetton_master_address = jetton_master_address
        self.jetton_amount = jetton_amount
        self.jetton_decimals = jetton_decimals
        self.min_amount = min_amount
        self.router_address = router_address
        self.pton_address = pton_address
        self.dex_version = dex_version
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        if self.dex_version is None and None in (self.router_address, self.pton_address):
            self.dex_version, self.router_address, self.pton_address = await get_stonfi_router_details(
                offer_address=self.jetton_master_address.to_str(),
                ask_address="ton",
                amount=self.jetton_amount,
                decimals=self.jetton_decimals,
                is_testnet=wallet.client.is_testnet,
            )
        if self.dex_version == 1:
            router_v1 = StonfiRouterV1(wallet.client, self.router_address, self.pton_address)
            to, value, body = await router_v1.get_swap_jetton_to_ton_tx_params(
                offer_jetton_address=self.jetton_master_address,
                user_wallet_address=wallet.address,
                offer_amount=to_nano(self.jetton_amount, self.jetton_decimals),
                min_ask_amount=to_nano(self.min_amount),
            )
        elif self.dex_version == 2:
            router_v2 = StonfiRouterV2(wallet.client, self.router_address, self.pton_address)
            to, value, body = await router_v2.get_swap_jetton_to_ton_tx_params(
                offer_jetton_address=self.jetton_master_address,
                receiver_address=wallet.address,
                user_wallet_address=wallet.address,
                offer_amount=to_nano(self.jetton_amount, self.jetton_decimals),
                min_ask_amount=to_nano(self.min_amount),
                refund_address=wallet.address,
            )
        else:
            raise ValueError(f"Unsupported STONfi Router version: {self.dex_version}")

        return wallet.create_wallet_internal_message(
            destination=to,
            value=value,
            body=body,
            bounce=True,
            **self.other,
        )


class DedustSwapJettonToJettonMessage(TransferMessageBase):
    """
    Data class for swapping jettons.

    :param from_jetton_master_address: The address of the jetton master contract from which to swap.
    :param to_jetton_master_address: The address of the jetton master contract to which to swap.
    :param jetton_amount: The amount of jettons to swap.
    :param min_amount: Minimum amount of amount to receive. Defaults to 0.
    :param from_jetton_decimals: The jetton decimals of the from_jetton_master_address (used for calculating jetton_amount).
    :param to_jetton_decimals: The jetton decimals of the to_jetton_master_address (used for calculating min_amount).
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            from_jetton_master_address: Union[Address, str],
            to_jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            min_amount: Union[int, float] = 0,
            from_jetton_decimals: int = 9,
            to_jetton_decimals: int = 9,
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> None:
        if isinstance(from_jetton_master_address, str):
            from_jetton_master_address = Address(from_jetton_master_address)
        if isinstance(to_jetton_master_address, str):
            to_jetton_master_address = Address(to_jetton_master_address)
        if isinstance(factory_address, str):
            factory_address = Address(factory_address)
        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        self.from_jetton_master_address = from_jetton_master_address
        self.to_jetton_master_address = to_jetton_master_address
        self.jetton_amount = jetton_amount
        self.min_amount = min_amount
        self.from_jetton_decimals = from_jetton_decimals
        self.to_jetton_decimals = to_jetton_decimals
        self.factory_address = factory_address
        self.native_vault_address = native_vault_address
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        factory = Factory(wallet.client, self.factory_address, self.native_vault_address)
        to, value, body = await factory.get_swap_jetton_to_jetton_tx_params(
            recipient_address=wallet.address,
            offer_jetton_address=self.from_jetton_master_address,
            ask_jetton_address=self.to_jetton_master_address,
            offer_amount=to_nano(self.jetton_amount, self.from_jetton_decimals),
            min_ask_amount=to_nano(self.min_amount, self.to_jetton_decimals),
        )

        return wallet.create_wallet_internal_message(
            destination=to,
            value=value,
            body=body,
            bounce=True,
            **self.other,
        )


class StonfiSwapJettonToJettonMessage(TransferMessageBase):
    """
    Data class for swapping jettons.

    :param from_jetton_master_address: The address of the jetton master contract from which to swap.
    :param to_jetton_master_address: The address of the jetton master contract to which to swap.
    :param jetton_amount: The amount of jettons to swap.
    :param min_amount: Minimum amount of amount to receive. Defaults to 0.
    :param from_jetton_decimals: The jetton decimals of the from_jetton_master_address (used for calculating jetton_amount).
    :param to_jetton_decimals: The jetton decimals of the to_jetton_master_address (used for calculating min_amount).
    :param kwargs: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            from_jetton_master_address: Union[Address, str],
            to_jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            min_amount: Union[int, float] = 0,
            from_jetton_decimals: int = 9,
            to_jetton_decimals: int = 9,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
            dex_version: Optional[int] = None,
            **kwargs,
    ) -> None:
        if isinstance(from_jetton_master_address, str):
            from_jetton_master_address = Address(from_jetton_master_address)
        if isinstance(to_jetton_master_address, str):
            to_jetton_master_address = Address(to_jetton_master_address)
        if isinstance(router_address, str):
            router_address = Address(router_address)
        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        self.from_jetton_master_address = from_jetton_master_address
        self.to_jetton_master_address = to_jetton_master_address
        self.jetton_amount = jetton_amount
        self.min_amount = min_amount
        self.from_jetton_decimals = from_jetton_decimals
        self.to_jetton_decimals = to_jetton_decimals
        self.router_address = router_address
        self.pton_address = pton_address
        self.dex_version = dex_version
        self.other = kwargs

    async def build(self, wallet: Wallet) -> WalletMessage:
        if self.dex_version is None and None in (self.router_address, self.pton_address):
            self.dex_version, self.router_address, _ = await get_stonfi_router_details(
                offer_address=self.from_jetton_master_address.to_str(),
                ask_address=self.to_jetton_master_address.to_str(),
                amount=self.jetton_amount,
                decimals=self.from_jetton_decimals,
                is_testnet=wallet.client.is_testnet,
            )
        if self.dex_version == 1:
            router_v1 = StonfiRouterV1(wallet.client, self.router_address, self.pton_address)
            to, value, body = await router_v1.get_swap_jetton_to_jetton_tx_params(
                user_wallet_address=wallet.address,
                offer_jetton_address=self.from_jetton_master_address,
                ask_jetton_address=self.to_jetton_master_address,
                offer_amount=to_nano(self.jetton_amount, self.from_jetton_decimals),
                min_ask_amount=to_nano(self.min_amount, self.to_jetton_decimals),
            )
        elif self.dex_version == 2:
            router_v2 = StonfiRouterV2(wallet.client, self.router_address, self.pton_address)
            to, value, body = await router_v2.get_swap_jetton_to_jetton_tx_params(
                user_wallet_address=wallet.address,
                receiver_address=wallet.address,
                refund_address=wallet.address,
                offer_jetton_address=self.from_jetton_master_address,
                ask_jetton_address=self.to_jetton_master_address,
                offer_amount=to_nano(self.jetton_amount, self.from_jetton_decimals),
                min_ask_amount=to_nano(self.min_amount, self.to_jetton_decimals),
            )
        else:
            raise ValueError(f"Unsupported STONfi Router version: {self.dex_version}")

        return wallet.create_wallet_internal_message(
            destination=to,
            value=value,
            body=body,
            bounce=True,
            **self.other,
        )


TransferMessageType = Union[
    TransferMessage,
    TransferNFTMessage,
    TransferJettonMessage,
    DedustSwapTONToJettonMessage,
    DedustSwapJettonToTONMessage,
    DedustSwapJettonToJettonMessage,
    StonfiSwapTONToJettonMessage,
    StonfiSwapJettonToTONMessage,
    StonfiSwapJettonToJettonMessage,
]
