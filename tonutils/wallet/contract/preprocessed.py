from __future__ import annotations

import time
from typing import List, Tuple, Union, Optional

from pytoniq_core import (
    Cell,
    WalletMessage,
    begin_cell, Address, )
from pytoniq_core.crypto.keys import mnemonic_new, mnemonic_to_private_key
from pytoniq_core.crypto.signature import sign_message

from ._base import Wallet
from ..data import (
    PreprocessedWalletV2Data,
)
from ..op_codes import *
from ...client import Client
from ...dns.utils import resolve_wallet_address


class PreprocessedWalletV2(Wallet):
    """
    A class representing a preprocessed wallet V2 in the TON blockchain.
    """
    CODE_HEX = "b5ee9c7241010101003d000076ff00ddd40120f90001d0d33fd30fd74ced44d0d3ffd70b0f20a4830fa90822c8cbffcb0fc9ed5444301046baf2a1f823bef2a2f910f2a3f800ed552e766412"  # noqa

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            **kwargs,
    ) -> None:
        super().__init__(client, public_key, private_key, **kwargs)

    @classmethod
    def create_data(
            cls,
            public_key: bytes,
            **kwargs,
    ) -> PreprocessedWalletV2Data:
        return PreprocessedWalletV2Data(public_key)

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            **kwargs,
    ) -> PreprocessedWalletV2:
        return super().from_private_key(client, private_key, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            **kwargs,
    ) -> Tuple[PreprocessedWalletV2, bytes, bytes, List[str]]:
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.split(" ")

        public_key, private_key = mnemonic_to_private_key(mnemonic)
        return cls(client, public_key, private_key, **kwargs), public_key, private_key, mnemonic

    @classmethod
    def create(
            cls,
            client: Client,
            **kwargs,
    ) -> Tuple[PreprocessedWalletV2, bytes, bytes, List[str]]:
        mnemonic = mnemonic_new(24)
        return cls.from_mnemonic(client, mnemonic, **kwargs)

    @classmethod
    async def get_seqno(
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> int:
        address = await resolve_wallet_address(client, address)
        raw_account = await cls.get_raw_account(client, address)
        seqno = 0
        if raw_account.data is not None:
            seqno = raw_account.data.begin_parse().skip_bits(256).load_uint(16)
        return seqno

    @classmethod
    async def get_public_key(  # type: ignore
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> Optional[int]:
        address = await resolve_wallet_address(client, address)
        raw_account = await cls.get_raw_account(client, address)
        public_key = None
        if raw_account.data is not None:
            _public_key = raw_account.data.begin_parse().load_bytes(32)
            public_key = int.from_bytes(_public_key, byteorder="big")
        return public_key

    @classmethod
    def pack_actions(cls, messages: List[WalletMessage]) -> Cell:
        """
        Packs a list of wallet messages into a single Cell.

        :param messages: A list of WalletMessage instances to pack.
        :return: A Cell containing the packed messages.
        """
        actions_cell = Cell.empty()

        for msg in messages:
            action = (
                begin_cell()
                .store_uint(ACTION_SEND_MSG_OPCODE, 32)
                .store_uint(msg.send_mode, 8)
                .store_ref(msg.message.serialize())
                .end_cell()
            )
            actions_cell = (
                begin_cell()
                .store_ref(actions_cell)
                .store_cell(action)
                .end_cell()
            )

        return actions_cell

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        assert len(messages) <= 255, "For preprocessed wallet v2, maximum messages amount is 255"

        seqno = kwargs.get("seqno", 0)
        valid_until = kwargs.get("valid_until", int(time.time()) + 3600)

        signing_message = (
            begin_cell()
            .store_uint(valid_until, 64)
            .store_uint(seqno, 16)
            .store_ref(self.pack_actions(messages))
            .end_cell()
        )
        signature = sign_message(signing_message.hash, private_key)

        return (
            begin_cell()
            .store_bytes(signature)
            .store_ref(signing_message)
            .end_cell()
        )


class PreprocessedWalletV2R1(Wallet):
    """
    A class representing a preprocessed wallet V2 R1 in the TON blockchain.
    """
    CODE_HEX = "b5ee9c7241010101003c000074ff00ddd40120f90001d0d33fd30fd74ced44d0d3ffd70b0f20a4a9380f22c8cbffcb0fc9ed5444301046baf2a1f823bef2a2f910f2a3f800ed55d91c357f"  # noqa

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            **kwargs,
    ) -> None:
        super().__init__(client, public_key, private_key, **kwargs)

    @classmethod
    def create_data(
            cls,
            public_key: bytes,
            **kwargs,
    ) -> PreprocessedWalletV2Data:
        return PreprocessedWalletV2Data(public_key)

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            **kwargs,
    ) -> PreprocessedWalletV2R1:
        return super().from_private_key(client, private_key, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            **kwargs,
    ) -> Tuple[PreprocessedWalletV2R1, bytes, bytes, List[str]]:
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.split(" ")

        public_key, private_key = mnemonic_to_private_key(mnemonic)
        return cls(client, public_key, private_key, **kwargs), public_key, private_key, mnemonic

    @classmethod
    def create(
            cls,
            client: Client,
            **kwargs,
    ) -> Tuple[PreprocessedWalletV2R1, bytes, bytes, List[str]]:
        mnemonic = mnemonic_new(24)
        return cls.from_mnemonic(client, mnemonic, **kwargs)

    @classmethod
    async def get_seqno(
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> int:
        address = await resolve_wallet_address(client, address)
        raw_account = await cls.get_raw_account(client, address)
        seqno = 0
        if raw_account.data is not None:
            seqno = raw_account.data.begin_parse().skip_bits(256).load_uint(16)
        return seqno

    @classmethod
    async def get_public_key(  # type: ignore
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> Optional[int]:
        address = await resolve_wallet_address(client, address)
        raw_account = await cls.get_raw_account(client, address)
        public_key = None
        if raw_account.data is not None:
            _public_key = raw_account.data.begin_parse().load_bytes(32)
            public_key = int.from_bytes(_public_key, byteorder="big")
        return public_key

    @classmethod
    def pack_actions(cls, messages: List[WalletMessage]) -> Cell:
        """
        Packs a list of wallet messages into a single Cell.

        :param messages: A list of WalletMessage instances to pack.
        :return: A Cell containing the packed messages.
        """
        actions_cell = Cell.empty()

        for msg in messages:
            action = (
                begin_cell()
                .store_uint(ACTION_SEND_MSG_OPCODE, 32)
                .store_uint(msg.send_mode, 8)
                .store_ref(msg.message.serialize())
                .end_cell()
            )
            actions_cell = (
                begin_cell()
                .store_ref(actions_cell)
                .store_cell(action)
                .end_cell()
            )

        return actions_cell

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        assert len(messages) <= 255, "For preprocessed wallet v2 r1, maximum messages amount is 255"

        seqno = kwargs.get("seqno", 0)
        valid_until = kwargs.get("valid_until", int(time.time()) + 3600)

        signing_message = (
            begin_cell()
            .store_uint(valid_until, 64)
            .store_uint(seqno, 16)
            .store_ref(self.pack_actions(messages))
            .end_cell()
        )
        signature = sign_message(signing_message.hash, private_key)

        return (
            begin_cell()
            .store_bytes(signature)
            .store_ref(signing_message)
            .end_cell()
        )
