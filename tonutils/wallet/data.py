from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Builder, Cell, Slice, TlbScheme, WalletMessage, HashMap, begin_cell, Address, StateInit


class TransferData:
    """
    Data class for transferring funds.

    :param destination: The destination address.
    :param amount: The amount to transfer.
    :param body: The body of the message. Defaults to an empty cell.
        If a string is provided, it will be used as a transaction comment.
    :param state_init: The state init data. Defaults to None.
    :param other: Additional arguments (e.g. bounce, bounced ...).
    """

    def __init__(
            self,
            destination: Union[Address, str],
            amount: Union[int, float],
            body: Optional[Union[Cell, str]] = Cell.empty(),
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


class TransferItemData:
    """
    Data class for transferring items.

    :param destination: The destination address.
    :param item_address: The item address.
    :param forward_payload: Optional forward payload.
        If a string is provided, it will be used as a transaction comment.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON. Defaults to 0.001.
        A notification will be sent to the new owner if the amount is greater than 0;
    :param amount: The amount to transfer. Defaults to 0.05.
    """

    def __init__(
            self,
            destination: Union[Address, str],
            item_address: Union[Address, str],
            forward_payload: Optional[Union[Cell, str]] = Cell.empty(),
            forward_amount: Optional[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
    ) -> None:
        if isinstance(destination, str):
            destination = Address(destination)

        if isinstance(item_address, str):
            item_address = Address(item_address)

        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(0, 32)
                .store_snake_string(forward_payload)
                .end_cell()
            )

        self.destination = destination
        self.item_address = item_address
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.amount = amount


class TransferJettonData:
    """
    Data class for transferring jettons.

    :param destination: The destination address.
    :param jetton_master_address: The jetton master address.
    :param jetton_amount: The amount of jettons to transfer.
    :param forward_payload: Optional forward payload.
        If a string is provided, it will be used as a transaction comment.
        If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
    :param forward_amount: Forward amount in TON. Defaults to 0.001.
        A notification will be sent to the new owner if the amount is greater than 0;
    :param amount: The amount to transfer. Defaults to 0.05.
    """

    def __init__(
            self,
            destination: Union[Address, str],
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            forward_payload: Optional[Union[Cell, str]] = Cell.empty(),
            forward_amount: Optional[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
    ) -> None:
        if isinstance(destination, str):
            destination = Address(destination)

        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

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
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.amount = amount


class WalletData(TlbScheme):

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def serialize(self) -> Cell:
        raise NotImplementedError

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletData:
        raise NotImplementedError


class WalletV3Data(WalletData):

    def __init__(
            self,
            public_key: bytes,
            seqno: Optional[int] = 0,
            wallet_id: Optional[int] = 698983191
    ) -> None:
        super().__init__(public_key=public_key)
        self.public_key = public_key
        self.seqno = seqno
        self.wallet_id = wallet_id

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
        pass


class WalletV4Data(WalletData):

    def __init__(
            self,
            public_key: bytes,
            seqno: Optional[int] = 0,
            wallet_id: Optional[int] = 698983191,
            plugins: Optional[Cell] = None,
    ) -> None:
        super().__init__(public_key=public_key)

        self.public_key = public_key
        self.seqno = seqno
        self.wallet_id = wallet_id
        self.plugins = plugins

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .store_dict(self.plugins)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV4Data:
        pass


class HighloadWalletV2Data(WalletData):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: Optional[int] = 698983191,
            last_cleaned: Optional[int] = 0,
    ) -> None:
        super().__init__(public_key=public_key)
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.last_cleaned = last_cleaned

    @classmethod
    def old_queries_serializer(cls, src: WalletMessage, dest: Builder) -> None:
        dest.store_cell(src.serialize())

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(self.wallet_id, 32)
            .store_uint(self.last_cleaned, 64)
            .store_bytes(self.public_key)
            .store_dict(
                HashMap(
                    key_size=64,
                    value_serializer=self.old_queries_serializer,
                ).serialize(),
            )
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> HighloadWalletV2Data:
        pass
