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
from ..data import (
    TransferData,
    TransferNFTData,
    TransferJettonData,
    HighloadWalletV2Data,
    HighloadWalletV3Data,
)
from ..op_codes import *
from ...client import (
    Client,
)
from ...utils import to_nano


class HighloadWalletV2(Wallet):
    """
    A class representing a highload wallet V2 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c720101090100e5000114ff00f4a413f4bcf2c80b010201200203020148040501eaf28308d71820d31fd33ff823aa1f5320b9f263ed44d0d31fd33fd3fff404d153608040f40e6fa131f2605173baf2a207f901541087f910f2a302f404d1f8007f8e16218010f4786fa5209802d307d43001fb009132e201b3e65b8325a1c840348040f4438ae63101c8cb1f13cb3fcbfff400c9ed54080004d03002012006070017bd9ce76a26869af98eb85ffc0041be5f976a268698f98e99fe9ff98fa0268a91040207a0737d098c92dbfc95dd1f140034208040f4966fa56c122094305303b9de2093333601926c21e2b3"  # noqa

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> HighloadWalletV2:
        return super().from_private_key(client, private_key, wallet_id=wallet_id, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[HighloadWalletV2, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id=wallet_id, **kwargs)

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[HighloadWalletV2, bytes, bytes, List[str]]:
        return super().create(client, wallet_id=wallet_id, **kwargs)

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
    async def get_timeout(cls, client: Client, address: Union[Address, str]) -> int:
        """
        Get the timeout of the wallet.
        """
        if isinstance(address, str):
            address = Address(address)

        method_result = await client.run_get_method(
            address=address.to_str(),
            method_name="get_timeout",
        )
        return method_result[0]

    @classmethod
    async def get_processed(
            cls,
            client: Client,
            address: Union[Address, str],
            query_id: int,
            need_clean: bool,
    ) -> bool:
        """
        Get is processed of the wallet.
        """
        if isinstance(address, str):
            address = Address(address)

        method_result = await client.run_get_method(
            address=address.to_str(),
            method_name="processed?",
            stack=[query_id, -1 if need_clean else 0],
        )
        return bool(method_result[0])

    @classmethod
    async def get_last_cleaned(cls, client: Client, address: Union[Address, str]) -> int:
        """
        Get the last cleaned time of the wallet.
        """
        if isinstance(address, str):
            address = Address(address)

        method_result = await client.run_get_method(
            address=address.to_str(),
            method_name="get_last_clean_time",
        )
        return method_result[0]

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            **kwargs,
    ) -> HighloadWalletV3:
        return super().from_private_key(client, private_key, wallet_id=wallet_id, timeout=timeout, **kwargs)

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            **kwargs,
    ) -> Tuple[HighloadWalletV3, bytes, bytes, List[str]]:
        return super().create(client, wallet_id=wallet_id, timeout=timeout, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            **kwargs,
    ) -> Tuple[HighloadWalletV3, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id=wallet_id, timeout=timeout, **kwargs)

    async def _create_deploy_msg(self) -> MessageAny:
        """
        Create a deployment message for the wallet.
        """
        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=[self.create_wallet_internal_message(self.address)],
        )

        return self.create_external_msg(
            dest=self.address,
            state_init=self.state_init,
            body=body,
        )

    async def raw_transfer(
            self,
            messages: Optional[List[WalletMessage]] = None,
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Perform a raw transfer operation.

        :param messages: A list of WalletMessage instances to be transferred.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :param kwargs: Additional arguments.
        :return: The hash of the raw transfer message.
        """
        return await super().raw_transfer(
            messages=messages,
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
            **kwargs,
        )

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        """
        Creates a raw transfer message for sending to the blockchain.

        :param private_key: The private key of the wallet.
        :param messages: A list of WalletMessage instances to be transferred.
        :param kwargs: Additional optional parameters:
            - send_mode: The send mode for the message. Defaults to 3.
            - query_id: The query ID for the transaction. If not provided, it will be calculated.
            - created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
            - timeout: Timeout for the message. Defaults to the wallet's timeout.
        :return: A Cell object containing the raw transfer message.
        """
        created_at = kwargs.get("created_at", None) or int(time.time() - 30)
        query_id = kwargs.get("query_id", None) or created_at % (1 << 23)
        timeout = kwargs.get("timeout", None) or self.timeout
        send_mode = kwargs.get("send_mode", None) or 3

        assert len(messages) <= 254 * 254, "For highload wallet v3, maximum messages amount is 254*254."
        assert created_at > 0, "Created at timestamp should be positive."
        assert query_id < (1 << 23), "Query ID is too large."
        assert timeout < (1 << 22), "Timeout is too long."
        assert timeout > 5, "Timeout is too short."

        if len(messages) == 1 and messages[0].message.init is None:
            message_to_send = messages[0]
        elif len(messages) > 0:
            message_to_send = self.pack_actions(messages, query_id, send_mode)
        else:
            raise ValueError("There should be at least one message.")

        signing_message = (
            begin_cell()
            .store_uint(self.wallet_id, 32)
            .store_ref(message_to_send.message.serialize())
            .store_uint(send_mode, 8)
            .store_uint(query_id, 23)
            .store_uint(created_at, 64)
            .store_uint(timeout, 22)
            .end_cell()
        )
        signature = sign_message(signing_message.hash, self.private_key)

        return (
            begin_cell()
            .store_bytes(signature)
            .store_ref(signing_message)
            .end_cell()
        )

    def pack_actions(
            self,
            messages: List[WalletMessage],
            query_id: int,
            send_mode: int = 3,
    ) -> WalletMessage:
        """
        Packs a list of wallet messages into a single message.

        :param messages: A list of WalletMessage instances to pack.
        :param query_id: The query ID for the transaction.
        :param send_mode: The send mode for the message. Defaults to 3.
        :return: A WalletMessage instance containing the packed messages.
        """
        message_per_pack = 253

        if len(messages) > message_per_pack:
            rest = self.pack_actions(messages[message_per_pack:], query_id, send_mode)
            messages = messages[:message_per_pack] + [rest]

        list_cell, value = Cell.empty(), 0

        for msg in messages:
            value += msg.message.info.value.grams
            msg = (
                begin_cell()
                .store_uint(ACTION_SEND_MSG_OPCODE, 32)
                .store_uint(msg.send_mode, 8)
                .store_ref(msg.message.serialize())
                .end_cell()
            )
            list_cell = (
                begin_cell()
                .store_ref(list_cell)
                .store_cell(msg)
                .end_cell()
            )

        return self.create_wallet_internal_message(
            destination=self.address,
            send_mode=send_mode,
            value=value,
            body=(
                begin_cell()
                .store_uint(INTERNAL_TRANSFER_OPCODE, 32)
                .store_uint(query_id, 64)
                .store_ref(list_cell)
                .end_cell()
            )
        )

    async def transfer(
            self,
            destination: Union[Address, str],
            amount: Union[int, float] = 0,
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Transfer funds to a destination address.

        :param destination: The destination address.
        :param amount: The amount to transfer. Defaults to 0.
        :param body: The body of the message. Defaults to an empty cell.
            If a string is provided, it will be used as a transaction comment.
        :param state_init: The state initialization. Defaults to None.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :param kwargs: Additional arguments.
        :return: The hash of the transfer message.
        """
        if isinstance(destination, str):
            destination = Address(destination)

        message_hash = await self.raw_transfer(
            messages=[
                self.create_wallet_internal_message(
                    destination=destination,
                    value=to_nano(amount),
                    body=body,
                    state_init=state_init,
                    **kwargs
                ),
            ],
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
        )

        return message_hash

    async def batch_transfer(
            self,
            data_list: List[TransferData],
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Perform a batch transfer operation.

        :param data_list: The list of transfer data.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :return: The hash of the batch transfer message.
        """
        return await super().batch_transfer(
            data_list=data_list,
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
            **kwargs,
        )

    async def transfer_nft(
            self,
            destination: Union[Address, str],
            nft_address: Union[Address, str],
            response_address: Optional[Union[Address, str]] = None,
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Transfer an NFT to a destination address.

        :param destination: The destination address.
        :param nft_address: The NFT item address.
        :param response_address: The address to receive the notification. Defaults to the destination address.
        :param forward_payload: Optional forward payload.
            If a string is provided, it will be used as a transaction comment.
            If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
        :param forward_amount: Forward amount in TON. Defaults to 0.001.
            A notification will be sent to the new owner if the amount is greater than 0;
        :param amount: The amount to transfer. Defaults to 0.05.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :param kwargs: Additional arguments.
        :return: The hash of the NFT transfer message.
        """
        return await super().transfer_nft(
            destination=destination,
            nft_address=nft_address,
            response_address=response_address,
            forward_payload=forward_payload,
            forward_amount=forward_amount,
            amount=amount,
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
            **kwargs,
        )

    async def batch_nft_transfer(
            self,
            data_list: List[TransferNFTData],
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Perform a batch NFT transfer operation.

        :param data_list: The list of NFT transfer data.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :param kwargs: Additional arguments.
        :return: The hash of the batch NFT transfer message.
        """
        return await super().batch_nft_transfer(
            data_list=data_list,
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
            **kwargs,
        )

    async def transfer_jetton(
            self,
            destination: Union[Address, str],
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Transfer a jetton to a destination address.

        :param destination: The destination address.
        :param jetton_master_address: The jetton master address.
        :param jetton_amount: The amount of jettons to transfer.
        :param jetton_decimals: The jetton decimals. Defaults to 9.
        :param forward_payload: Optional forward payload.
            If a string is provided, it will be used as a transaction comment.
            If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
        :param forward_amount: Forward amount in TON. Defaults to 0.001.
            A notification will be sent to the new owner if the amount is greater than 0;
        :param amount: The amount to transfer. Defaults to 0.05.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :param kwargs: Additional arguments.
        :return: The hash of the jetton transfer message.
        """
        return await super().transfer_jetton(
            destination=destination,
            jetton_master_address=jetton_master_address,
            jetton_amount=jetton_amount,
            jetton_decimals=jetton_decimals,
            forward_payload=forward_payload,
            forward_amount=forward_amount,
            amount=amount,
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
            **kwargs,
        )

    async def batch_jetton_transfer(
            self,
            data_list: List[TransferJettonData],
            send_mode: Optional[int] = None,
            query_id: Optional[int] = None,
            created_at: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Perform a batch jetton transfer operation.

        :param data_list: The list of jetton transfer data.
        :param send_mode: The send mode. Defaults to 3.
        :param query_id: The query ID for the transaction. If not provided, it will be calculated.
        :param created_at: Timestamp when the message was created. Defaults to current time minus 30 seconds.
        :param timeout: Timeout for the message. Defaults to the wallet's timeout.
        :param kwargs: Additional arguments.
        :return: The hash of the batch jetton transfer message.
        """
        return await super().batch_jetton_transfer(
            data_list=data_list,
            send_mode=send_mode,
            query_id=query_id,
            created_at=created_at,
            timeout=timeout,
            **kwargs,
        )
