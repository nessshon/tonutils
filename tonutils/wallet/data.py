from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Address, Builder, Cell, Slice, StateInit, TlbScheme, begin_cell


class TransferData:
    """
    Data class for transferring funds.

    :param destination: The destination address.
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
        if isinstance(destination, str):
            destination = Address(destination)

        self.destination = destination
        self.amount = amount
        self.body = body
        self.state_init = state_init
        self.other = kwargs


class TransferNFTData:
    """
    Data class for transferring NFT.

    :param destination: The destination address.
    :param nft_address: The NFT item address.
    :param response_address: The address to receive the notification. Defaults to the destination address.
    :param forward_payload: Optional forward payload.
        If a string is provided, it will be used as a transaction comment.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON. Defaults to 0.001.
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
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
            **kwargs,
    ) -> None:
        if isinstance(destination, str):
            destination = Address(destination)

        if isinstance(nft_address, str):
            nft_address = Address(nft_address)

        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(0, 32)
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


class TransferJettonData:
    """
    Data class for transferring jettons.

    :param destination: The destination address.
    :param jetton_master_address: The jetton master address.
    :param jetton_amount: The amount of jettons to transfer.
    :param jetton_decimals: The jetton decimals. Defaults to 9.
    :param jetton_wallet_address: Optional jetton wallet address.
    :param forward_payload: Optional forward payload.
        If a string is provided, it will be used as a transaction comment.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON. Defaults to 0.001.
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
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
            **kwargs,
    ) -> None:
        if isinstance(destination, str):
            destination = Address(destination)

        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(jetton_wallet_address, str):
            jetton_wallet_address = Address(jetton_wallet_address)

        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(0, 32)
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


class SwapTONToJettonData:
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
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        self.jetton_master_address = jetton_master_address
        self.ton_amount = ton_amount
        self.min_amount = min_amount
        self.jetton_decimals = jetton_decimals
        self.forward_amount = forward_amount
        self.other = kwargs


class SwapJettonToTONData:
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
            **kwargs,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        self.jetton_master_address = jetton_master_address
        self.jetton_amount = jetton_amount
        self.jetton_decimals = jetton_decimals
        self.min_amount = min_amount
        self.other = kwargs


class SwapJettonToJettonData:
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
            **kwargs,
    ) -> None:
        if isinstance(from_jetton_master_address, str):
            from_jetton_master_address = Address(from_jetton_master_address)

        if isinstance(to_jetton_master_address, str):
            to_jetton_master_address = Address(to_jetton_master_address)

        self.from_jetton_master_address = from_jetton_master_address
        self.to_jetton_master_address = to_jetton_master_address
        self.jetton_amount = jetton_amount
        self.min_amount = min_amount
        self.from_jetton_decimals = from_jetton_decimals
        self.to_jetton_decimals = to_jetton_decimals
        self.other = kwargs


class WalletV2Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_bytes(self.public_key)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV3Data:
        raise NotImplementedError


class WalletV3Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.seqno = seqno

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV3Data:
        raise NotImplementedError


class WalletV4Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno
        self.wallet_id = wallet_id

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .store_bool(False)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV4Data:
        raise NotImplementedError


class WalletV5Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 0,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno
        self.wallet_id = wallet_id

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(1, 1)
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .store_bool(False)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV5Data:
        raise NotImplementedError


class HighloadWalletV2Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            last_cleaned: int = 0,
    ) -> None:
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.last_cleaned = last_cleaned

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(self.wallet_id, 32)
            .store_uint(self.last_cleaned, 64)
            .store_bytes(self.public_key)
            .store_uint(0, 1)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> HighloadWalletV2Data:
        raise NotImplementedError


class HighloadWalletV3Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            last_cleaned: int = 0,
    ) -> None:
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.timeout = timeout
        self.last_cleaned = last_cleaned

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_bytes(self.public_key)
            .store_uint(self.wallet_id, 32)
            .store_uint(self.last_cleaned, 64)
            .store_uint(0, 1)
            .store_uint(0, 1)
            .store_uint(self.timeout, 22)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> HighloadWalletV2Data:
        raise NotImplementedError


class PreprocessedWalletV2Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_bytes(self.public_key)
            .store_uint(self.seqno, 16)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> PreprocessedWalletV2Data:
        raise NotImplementedError
