from __future__ import annotations

import time
from typing import List, Optional, Tuple, Union

from pytoniq_core import (
    Builder,
    Cell,
    HashMap,
    MessageAny,
    WalletMessage,
    begin_cell,
)
from pytoniq_core.crypto.signature import sign_message

from ...client import Client
from ...utils import message_to_boc_hex
from ...wallet import Wallet
from ...wallet.data import (
    TransferData,
    TransferItemData,
    TransferJettonData,
    HighloadWalletV2Data,
)


class HighloadWalletV2(Wallet):
    """
    A class representing a highload wallet V2 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c720101090100e5000114ff00f4a413f4bcf2c80b010201200203020148040501eaf28308d71820d31fd33ff823aa1f5320b9f263ed44d0d31fd33fd3fff404d153608040f40e6fa131f2605173baf2a207f901541087f910f2a302f404d1f8007f8e16218010f4786fa5209802d307d43001fb009132e201b3e65b8325a1c840348040f4438ae63101c8cb1f13cb3fcbfff400c9ed54080004d03002012006070017bd9ce76a26869af98eb85ffc0041be5f976a268698f98e99fe9ff98fa0268a91040207a0737d098c92dbfc95dd1f140034208040f4966fa56c122094305303b9de2093333601926c21e2b3"  # noqa

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            wallet_id: Optional[int] = 698983191,
    ) -> None:
        """
        Initialize a HighloadWalletV2 instance.

        :param client: The client to interact with the blockchain.
        :param public_key: The public key of the wallet.
        :param private_key: The private key of the wallet.
        :param wallet_id: The wallet ID. Defaults to 698983191.
        """
        super().__init__(
            client=client,
            public_key=public_key,
            private_key=private_key,
            wallet_id=wallet_id,
        )
        self._data = self._create_data(public_key, wallet_id).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create(cls) -> Tuple[HighloadWalletV2, bytes, bytes, List[str]]:
        """
        Create a new HighloadWalletV2 instance.

        :return: A tuple containing the wallet instance, public key, private key, and mnemonic.
        """
        return super().create()  # type: ignore

    @classmethod
    def from_mnemonic(
            cls,
            mnemonic: Union[List[str], str],
            client: Optional[Client] = None,
    ) -> Tuple[HighloadWalletV2, bytes, bytes, List[str]]:
        """
        Create a HighloadWalletV2 instance from a mnemonic.

        :param mnemonic: The mnemonic phrase.
        :param client: The client to interact with the blockchain.
        :return: A tuple containing the wallet instance, public key, private key, and mnemonic.
        """
        return super().from_mnemonic(mnemonic, client)  # type: ignore

    @classmethod
    def _create_data(cls, public_key: bytes, wallet_id: int) -> HighloadWalletV2Data:  # noqa
        """
        Create wallet data for HighloadWalletV2.

        :param public_key: The public key of the wallet.
        :param wallet_id: The wallet ID.
        :return: An instance of HighloadWalletV2Data.
        """
        return HighloadWalletV2Data(public_key=public_key, wallet_id=wallet_id)

    async def _create_deploy_msg(self) -> MessageAny:
        """
        Create the deployment message for the wallet.
        """
        body = self._raw_create_transfer_msg(
            private_key=self.private_key,
            messages=[],
        )

        return self._create_external_msg(
            dest=self.address,
            state_init=self.state_init,
            body=body,
        )

    def _raw_create_transfer_msg(  # noqa
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            wallet_id: Optional[int] = 698983191,
            query_id: Optional[int] = 0,
            offset: Optional[int] = 7200,
    ) -> Cell:
        """
        Create a raw transfer message.

        :param private_key: The private key of the wallet.
        :param messages: A list of wallet messages.
        :param wallet_id: The wallet ID. Defaults to 698983191.
        :param query_id: The query ID. Defaults to 0.
        :param offset: The offset for generating the query ID. Defaults to 7200.
        :return: A Cell containing the raw transfer message.
        """
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
        assert len(messages) <= 254, 'for highload wallet maximum messages amount is 254'

        body = self._raw_create_transfer_msg(
            private_key=self.private_key,
            messages=messages or [],
        )

        message = self._create_external_msg(dest=self.address, body=body)
        message_boc_hex, message_hash = message_to_boc_hex(message)
        await self.client.send_message(message_boc_hex)

        return message_hash

    async def transfer(self, data_list: List[TransferData]) -> str:  # noqa
        """
        Perform a transfer operation.

        :param data_list: A list of transfer data.
        :return: The hash of the transfer message.
        """
        return await self.batch_transfer(data_list)

    async def transfer_nft(self, data_list: List[TransferItemData]) -> str:  # noqa
        """
        Perform a transfer operation for NFTs.

        :param data_list: A list of NFT transfer data.
        :return: The hash of the NFT transfer message.
        """
        return await self.batch_nft_transfer(data_list)

    async def transfer_jetton(self, data_list: List[TransferJettonData]) -> str:  # noqa
        """
        Perform a transfer operation for jettons.

        :param data_list: A list of jetton transfer data.
        :return: The hash of the jetton transfer message.
        """
        return await self.batch_jetton_transfer(data_list)
