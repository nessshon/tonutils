from __future__ import annotations

import time
from typing import List, Optional, Tuple, Union

from pytoniq_core import (
    Address,
    Builder,
    Cell,
    MessageAny,
    HashMap,
    StateInit,
    WalletMessage,
    begin_cell,
)
from pytoniq_core.crypto.signature import sign_message

from ._base import Wallet
from ...client import Client
from ...wallet.data import HighloadWalletV2Data, HighloadWalletV3Data


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
        assert len(messages) <= 254, 'For highload wallet, maximum messages amount is 254'

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

    async def transfer(
            self,
            destination: Union[Address, str],
            amount: Union[int, float] = 0,
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
            **kwargs,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_transfer' method instead")

    async def transfer_nft(
            self,
            destination: Union[Address, str],
            nft_address: Union[Address, str],
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
            **kwargs,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_transfer_nft' method instead")

    async def transfer_jetton(
            self,
            destination: Union[Address, str],
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
            **kwargs,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_transfer_jetton' method instead")

    async def dedust_swap_jetton_to_ton(
            self,
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            amount: Union[int, float] = 0.3,
            forward_amount: Union[int, float] = 0.25,
            **kwargs,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_dedust_swap_jetton_to_ton' method instead")

    async def dedust_swap_ton_to_jetton(
            self,
            jetton_master_address: Union[Address, str],
            ton_amount: Union[int, float],
            amount: Union[int, float] = 0.25,
            **kwargs,
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
            **kwargs,
    ) -> str:
        raise NotImplementedError("Not implemented yet, use 'batch_dedust_swap_jetton_to_jetton' method instead")


class HighloadWalletV3(Wallet):
    """
    A class representing a highload wallet V3 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c7241021001000228000114ff00f4a413f4bcf2c80b01020120020d02014803040078d020d74bc00101c060b0915be101d0d3030171b0915be0fa4030f828c705b39130e0d31f018210ae42e5a4ba9d8040d721d74cf82a01ed55fb04e030020120050a02027306070011adce76a2686b85ffc00201200809001aabb6ed44d0810122d721d70b3f0018aa3bed44d08307d721d70b1f0201200b0c001bb9a6eed44d0810162d721d70b15800e5b8bf2eda2edfb21ab09028409b0ed44d0810120d721f404f404d33fd315d1058e1bf82325a15210b99f326df82305aa0015a112b992306dde923033e2923033e25230800df40f6fa19ed021d721d70a00955f037fdb31e09130e259800df40f6fa19cd001d721d70a00937fdb31e0915be270801f6f2d48308d718d121f900ed44d0d3ffd31ff404f404d33fd315d1f82321a15220b98e12336df82324aa00a112b9926d32de58f82301de541675f910f2a106d0d31fd4d307d30cd309d33fd315d15168baf2a2515abaf2a6f8232aa15250bcf2a304f823bbf2a35304800df40f6fa199d024d721d70a00f2649130e20e01fe5309800df40f6fa18e13d05004d718d20001f264c858cf16cf8301cf168e1030c824cf40cf8384095005a1a514cf40e2f800c94039800df41704c8cbff13cb1ff40012f40012cb3f12cb15c9ed54f80f21d0d30001f265d3020171b0925f03e0fa4001d70b01c000f2a5fa4031fa0031f401fa0031fa00318060d721d300010f0020f265d2000193d431d19130e272b1fb00b585bf03"  # noqa

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            **kwargs,
    ) -> None:
        self.timeout = timeout
        super().__init__(client, public_key, private_key, wallet_id, **kwargs)

    @classmethod
    def create_data(
            cls,
            public_key: bytes,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
    ) -> HighloadWalletV3Data:
        return HighloadWalletV3Data(public_key, wallet_id, timeout)

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            **kwargs,
    ) -> Tuple[HighloadWalletV3, bytes, bytes, List[str]]:
        return super().create(client, wallet_id, **kwargs)

    async def _create_deploy_msg(self) -> MessageAny:
        """
        Create a deployment message for the wallet.
        """
        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=[],
        )

        return self.create_external_msg(
            dest=self.address,
            state_init=self.state_init,
            body=body,
        )

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            **kwargs,
    ) -> Tuple[HighloadWalletV3, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id, timeout=timeout, **kwargs)

    async def raw_transfer(
            self,
            messages: Optional[List[WalletMessage]] = None,
            **kwargs,
    ) -> str:
        raise NotImplementedError

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        raise NotImplementedError

    @classmethod
    def pack_actions(cls, messages: List[WalletMessage]) -> Tuple[int, Cell]:
        raise NotImplementedError
