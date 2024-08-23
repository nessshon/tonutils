from __future__ import annotations

import time
from typing import List, Optional, Tuple, Union

from pytoniq_core import (
    Address,
    Builder,
    Cell,
    HashMap,
    MessageAny,
    StateInit,
    WalletMessage,
    begin_cell,
)
from pytoniq_core.crypto.signature import sign_message

from ._base import Wallet
from ...client import Client
from ...utils import message_to_boc_hex
from ...wallet.data import HighloadWalletV2Data


class HighloadWalletV2(Wallet):
    """
    A class representing a highload wallet V2 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c720101090100e5000114ff00f4a413f4bcf2c80b010201200203020148040501eaf28308d71820d31fd33ff823aa1f5320b9f263ed44d0d31fd33fd3fff404d153608040f40e6fa131f2605173baf2a207f901541087f910f2a302f404d1f8007f8e16218010f4786fa5209802d307d43001fb009132e201b3e65b8325a1c840348040f4438ae63101c8cb1f13cb3fcbfff400c9ed54080004d03002012006070017bd9ce76a26869af98eb85ffc0041be5f976a268698f98e99fe9ff98fa0268a91040207a0737d098c92dbfc95dd1f140034208040f4966fa56c122094305303b9de2093333601926c21e2b3"  # noqa

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[HighloadWalletV2, bytes, bytes, List[str]]:
        return super().create(client, wallet_id, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[HighloadWalletV2, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id, **kwargs)

    @classmethod
    def create_data(
            cls,
            public_key: bytes,
            wallet_id: int = 698983191,
            last_cleaned: int = 0,
    ) -> HighloadWalletV2Data:
        return HighloadWalletV2Data(public_key, wallet_id, last_cleaned)

    async def _create_deploy_msg(self) -> MessageAny:
        """
        Create the deployment message for the wallet.
        """
        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=[],
        )

        return self._create_external_msg(
            dest=self.address,
            state_init=self.state_init,
            body=body,
        )

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        """
        Create a raw transfer message.

        :param private_key: The private key of the wallet.
        :param messages: A list of wallet messages.
        :param kwargs: Additional optional parameters:
            - wallet_id: The wallet ID. Defaults to 698983191.
            - query_id: The query ID. Defaults to 0.
            - offset: The offset for generating the query ID. Defaults to 7200.
        :return: A Cell containing the raw transfer message.
        """

        wallet_id = kwargs.get("wallet_id", 698983191)
        query_id = kwargs.get("query_id", 0)
        offset = kwargs.get("offset", 7200)

        signing_message = begin_cell().store_uint(wallet_id, 32)

        if not query_id:
            signing_message.store_uint(int(time.time() + offset) << 32, 64)
        else:
            signing_message.store_uint(query_id, 64)

        def value_serializer(src: WalletMessage, dest: Builder) -> None:
            dest.store_cell(src.serialize())

        messages_dict = HashMap(key_size=16, value_serializer=value_serializer)

        for i in range(len(messages)):
            messages_dict.set_int_key(i, messages[i])

        signing_message.store_dict(messages_dict.serialize())

        signing_message = signing_message.end_cell()
        signature = sign_message(signing_message.hash, private_key)

        return (
            begin_cell()
            .store_bytes(signature)
            .store_cell(signing_message)
            .end_cell()
        )

    async def _raw_transfer(
            self,
            messages: Optional[List[WalletMessage]] = None,
    ) -> str:
        """
        Perform a raw transfer operation.

        :param messages: A list of wallet messages. Defaults to None.
        :return: The hash of the raw transfer message.
        """
        if messages is None:
            messages = []

        assert len(messages) <= 254, 'for highload wallet maximum messages amount is 254'

        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=messages or [],
        )

        message = self._create_external_msg(dest=self.address, body=body)
        message_boc_hex, message_hash = message_to_boc_hex(message)
        await self.client.send_message(message_boc_hex)

        return message_hash

    async def transfer(
            self,
            destination: Union[Address, str],
            amount: Union[int, float] = 0,
            body: Union[Cell, str] = Cell.empty(),
            state_init: Optional[StateInit] = None,
            **kwargs
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_transfer' method instead")

    async def transfer_nft(
            self,
            destination: Union[Address, str],
            nft_address: Union[Address, str],
            forward_payload: Union[Cell, str] = Cell.empty(),
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_transfer_nft' method instead")

    async def transfer_jetton(
            self,
            destination: Union[Address, str],
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            forward_payload: Union[Cell, str] = Cell.empty(),
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_transfer_jetton' method instead")

    async def dedust_swap_jetton_to_ton(
            self,
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            amount: Union[int, float] = 0.3,
            forward_amount: Union[int, float] = 0.25,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_dedust_swap_jetton_to_ton' method instead")

    async def dedust_swap_ton_to_jetton(
            self,
            jetton_master_address: Union[Address, str],
            ton_amount: Union[int, float],
            amount: Union[int, float] = 0.25,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_dedust_swap_ton_to_jetton' method instead")

    async def dedust_swap_jetton_to_jetton(
            self,
            from_jetton_master_address: Union[Address, str],
            to_jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            amount: Union[int, float] = 0.3,
            forward_amount: Union[int, float] = 0.25,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_dedust_swap_jetton_to_jetton' method instead")
