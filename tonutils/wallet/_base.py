from __future__ import annotations

import time
from typing import Optional, List, Union, Tuple

from pytoniq_core import (
    Address,
    Cell,
    StateInit,
    MessageAny,
    WalletMessage,
    begin_cell,
)
from pytoniq_core.crypto.keys import (
    mnemonic_new,
    mnemonic_to_private_key,
)
from pytoniq_core.crypto.signature import sign_message

from .data import (
    WalletV3Data,
    WalletV4Data,
    HighloadWalletV2Data,
    TransferData,
    TransferItemData,
    TransferJettonData,
)
from ..client import (
    Client,
    LiteClient,
    TonapiClient,
    ToncenterClient,
)
from ..contract import Contract
from ..exceptions import UnknownClientError
from ..jetton import Jetton
from ..nft import ItemStandard
from ..utils import (
    create_encrypted_comment_cell,
    message_to_boc_hex, amount_to_nano,
)


class Wallet(Contract):
    """
    A class representing a TON blockchain wallet.
    """

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            wallet_id: Optional[int] = 698983191,
    ) -> None:
        """
        Initialize a Wallet instance.

        :param client: The client to interact with the blockchain.
        :param public_key: The public key of the wallet.
        :param private_key: The private key of the wallet.
        :param wallet_id: The ID of the wallet. Defaults to 698983191.
        """
        self.client = client
        self.public_key = public_key
        self.private_key = private_key
        self.wallet_id = wallet_id

        self._data = self._create_data(public_key, wallet_id=wallet_id).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def _create_data(
            cls,
            public_key: bytes,
            seqno: Optional[int] = 0,
            wallet_id: Optional[int] = 698983191,
            **kwargs,
    ) -> Union[WalletV3Data | WalletV4Data, HighloadWalletV2Data]:
        """
        Create wallet data.

        :param public_key: The public key of the wallet.
        :param seqno: The sequence number. Defaults to 0.
        :param wallet_id: The wallet ID. Defaults to 698983191.
        :param kwargs: Additional arguments.
        :return: Wallet data instance.
        """
        raise NotImplementedError

    async def _create_deploy_msg(self) -> MessageAny:
        """
        Create a deployment message for the wallet.
        """
        body = self._raw_create_transfer_msg(
            private_key=self.private_key,
            seqno=0,
            messages=[],
        )

        return self._create_external_msg(
            dest=self.address,
            state_init=self.state_init,
            body=body,
        )

    def _raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            seqno: Optional[int] = 0,
            wallet_id: Optional[int] = 698983191,
            valid_until: Optional[int] = None,
            op_code: Optional[int] = None,
    ) -> Cell:
        """
        Create a raw transfer message.

        :param private_key: The private key to sign the message.
        :param messages: The list of wallet messages.
        :param seqno: The sequence number. Defaults to 0.
        :param wallet_id: The wallet ID. Defaults to 698983191.
        :param valid_until: The validity timestamp. Defaults to None.
        :param op_code: The operation code. Defaults to None.
        :return: The serialized message cell.
        """
        signing_message = begin_cell().store_uint(wallet_id, 32)

        if seqno == 0:
            signing_message.store_bits('1' * 32)
        else:
            if valid_until is not None:
                signing_message.store_uint(valid_until, 32)
            else:
                signing_message.store_uint(int(time.time()) + 60, 32)

        signing_message.store_uint(seqno, 32)

        if op_code is not None:
            signing_message.store_uint(op_code, 8)

        for m in messages:
            signing_message.store_cell(m.serialize())

        signing_message = signing_message.end_cell()
        signature = sign_message(signing_message.hash, private_key)

        return (
            begin_cell()
            .store_bytes(signature)
            .store_cell(signing_message)
            .end_cell()
        )

    @classmethod
    def create_wallet_internal_message(
            cls,
            destination: Address,
            send_mode: Optional[int] = 3,
            value: Optional[int] = 0,
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
            **kwargs,
    ) -> WalletMessage:
        """
        Create an internal wallet message.

        :param destination: The destination address.
        :param send_mode: The send mode. Defaults to 3.
        :param value: The value to transfer. Defaults to 0.
        :param body: The body of the message. Defaults to None.
        :param state_init: The state initialization. Defaults to None.
        :param kwargs: Additional arguments.
        :return: The wallet message.
        """
        if isinstance(body, str):
            body = (
                begin_cell()
                .store_uint(0, 32)
                .store_snake_string(body)
                .end_cell()
            )

        message = cls._create_internal_msg(
            dest=destination,
            value=value,
            body=body,
            state_init=state_init,
            **kwargs,
        )

        return WalletMessage(
            send_mode=send_mode,
            message=message,
        )

    @classmethod
    def from_mnemonic(
            cls,
            mnemonic: Union[List[str], str],
            client: Optional[Client] = None,
    ) -> Tuple[Wallet, bytes, bytes, List[str]]:
        """
        Create a wallet from a mnemonic phrase.

        :param mnemonic: The mnemonic phrase.
        :param client: The client to interact with the blockchain. Defaults to None.
        :return: A tuple containing the wallet instance, public key, private key, and mnemonic phrase.
        """
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.split(" ")

        public_key, private_key = mnemonic_to_private_key(mnemonic)
        return cls(client, public_key, private_key), public_key, private_key, mnemonic

    @classmethod
    def create(cls) -> Tuple[Wallet, bytes, bytes, List[str]]:
        """
        Create a new wallet.

        :return: A tuple containing the wallet instance, public key, private key, and mnemonic phrase.
        """
        mnemonic = mnemonic_new(24)
        return cls.from_mnemonic(mnemonic)

    async def deploy(self) -> str:
        """
        Deploy the wallet to the blockchain.
        """
        message = await self._create_deploy_msg()
        message_boc_hex, message_hash = message_to_boc_hex(message)
        await self.client.send_message(message_boc_hex)

        return message_hash

    async def get_seqno(self, address: Optional[Union[Address, str]] = None) -> int:
        """
        Get the sequence number (seqno) of the wallet.
        """
        if address is None:
            address = self.address.to_str()
        else:
            if isinstance(address, Address):
                address = address.to_str()

        method_result = await self.client.run_get_method(
            address=address,
            method_name="seqno",
        )

        if isinstance(self.client, TonapiClient):
            seqno = int(method_result["decoded"]["state"] or 0)
        elif isinstance(self.client, ToncenterClient):
            seqno = int(method_result["stack"][0]["value"], 16)
        elif isinstance(self.client, LiteClient):
            seqno = int(method_result[0])
        else:
            raise UnknownClientError(self.client.__class__.__name__)

        return seqno

    async def get_public_key(self, address: Union[Address, str]) -> int:
        if address is None:
            address = self.address.to_str()
        else:
            if isinstance(address, Address):
                address = address.to_str()

        method_result = await self.client.run_get_method(
            address=address,
            method_name="get_public_key",
        )

        if isinstance(self.client, TonapiClient):
            seqno = int(method_result["decoded"]["public_key"] or 0)
        elif isinstance(self.client, ToncenterClient):
            seqno = int(method_result["stack"][0]["value"], 16)
        elif isinstance(self.client, LiteClient):
            seqno = int(method_result[0])
        else:
            raise UnknownClientError(self.client.__class__.__name__)

        return seqno

    async def _raw_transfer(
            self,
            messages: Optional[List[WalletMessage]] = None,
    ) -> str:
        """
        Perform a raw transfer operation.

        :param messages: The list of wallet messages to transfer.
        :return: The hash of the transfer message.
        """
        assert len(messages) <= 4, 'For common wallet maximum messages amount is 4'
        seqno = await self.get_seqno()

        body = self._raw_create_transfer_msg(
            private_key=self.private_key,
            seqno=seqno,
            messages=messages or [],
        )

        message = self._create_external_msg(dest=self.address, body=body)
        message_boc_hex, message_hash = message_to_boc_hex(message)
        await self.client.send_message(message_boc_hex)

        return message_hash

    async def transfer(
            self,
            destination: Union[Address, str],
            amount: Optional[Union[int, float]] = 0,
            body: Optional[Cell, str] = Cell.empty(),
            state_init: Optional[StateInit] = None,
            **kwargs
    ) -> str:
        """
        Transfer funds to a destination address.

        :param destination: The destination address.
        :param amount: The amount to transfer. Defaults to 0.
        :param body: The body of the message. Defaults to an empty cell.
            If a string is provided, it will be used as a transaction comment.
        :param state_init: The state initialization. Defaults to None.
        :param kwargs: Additional arguments.
        :return: The hash of the transfer message.
        """
        if isinstance(destination, str):
            destination = Address(destination)

        message_hash = await self._raw_transfer(
            messages=[
                self.create_wallet_internal_message(
                    destination=destination,
                    value=amount_to_nano(amount),
                    body=body,
                    state_init=state_init,
                    **kwargs
                ),
            ],
        )

        return message_hash

    async def batch_transfer(self, data_list: List[TransferData]) -> str:
        """
        Perform a batch transfer operation.

        :param data_list: The list of transfer data.
        :return: The hash of the batch transfer message.
        """
        messages = [
            self.create_wallet_internal_message(
                destination=data.destination,
                value=amount_to_nano(data.amount),
                body=data.body,
                state_init=data.state_init,
                **data.other,
            ) for data in data_list
        ]

        message_hash = await self._raw_transfer(messages=messages)

        return message_hash

    async def transfer_nft(
            self,
            destination: Union[Address, str],
            item_address: Union[Address, str],
            forward_payload: Optional[Cell, str] = Cell.empty(),
            forward_amount: Optional[int, float] = 0.001,
            amount: Optional[Union[int, float]] = 0.05,
    ) -> str:
        """
        Transfer an NFT to a destination address.

        :param destination: The destination address.
        :param item_address: The NFT item address.
        :param forward_payload: Optional forward payload.
            If a string is provided, it will be used as a transaction comment.
            If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
        :param forward_amount: Forward amount in TON. Defaults to 0.001.
            A notification will be sent to the new owner if the amount is greater than 0;
        :param amount: The amount to transfer. Defaults to 0.05.
        :return: The hash of the NFT transfer message.
        """
        if isinstance(destination, str):
            destination = Address(destination)
        if isinstance(item_address, str):
            item_address = Address(item_address)

        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(0, 32)
                .store_string(forward_payload)
                .end_cell()
            )

        message_hash = await self.transfer(
            destination=item_address,
            amount=amount,
            body=ItemStandard.build_transfer_body(
                new_owner_address=destination,
                forward_payload=forward_payload,
                forward_amount=amount_to_nano(forward_amount),
            ),
        )

        return message_hash

    async def batch_nft_transfer(self, data_list: List[TransferItemData]) -> str:
        """
        Perform a batch NFT transfer operation.

        :param data_list: The list of NFT transfer data.
        :return: The hash of the batch NFT transfer message.
        """
        messages = [
            self.create_wallet_internal_message(
                destination=data.item_address,
                value=amount_to_nano(data.amount),
                body=ItemStandard.build_transfer_body(
                    new_owner_address=data.destination,
                    forward_payload=data.forward_payload,
                    forward_amount=data.forward_amount,
                ),
            ) for data in data_list
        ]

        message_hash = await self._raw_transfer(messages=messages)

        return message_hash

    async def transfer_jetton(
            self,
            destination: Union[Address, str],
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            forward_payload: Optional[Cell, str] = Cell.empty(),
            forward_amount: Optional[int, float] = 0.001,
            amount: Optional[Union[int, float]] = 0.05,
    ) -> str:
        """
        Transfer a jetton to a destination address.

        :param destination: The destination address.
        :param jetton_master_address: The jetton master address.
        :param jetton_amount: The amount of jettons to transfer.
        :param forward_payload: Optional forward payload.
            If a string is provided, it will be used as a transaction comment.
            If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
        :param forward_amount: Forward amount in TON. Defaults to 0.001.
            A notification will be sent to the new owner if the amount is greater than 0;
        :param amount: The amount to transfer. Defaults to 0.05.
        :return: The hash of the jetton transfer message.
        """
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

        jetton_wallet_address = await Jetton(self.client).get_jetton_wallet_address(
            jetton_master_address=jetton_master_address.to_str(),
            owner_address=self.address.to_str(),
        )

        message_hash = await self.transfer(
            destination=jetton_wallet_address,
            amount=amount,
            body=Jetton.build_transfer_body(
                recipient_address=destination,
                response_address=self.address,
                jetton_amount=amount_to_nano(jetton_amount),
                forward_payload=forward_payload,
                forward_amount=amount_to_nano(forward_amount),
            )
        )

        return message_hash

    async def batch_jetton_transfer(self, data_list: List[TransferJettonData]) -> str:
        """
        Perform a batch jetton transfer operation.

        :param data_list: The list of jetton transfer data.
        :return: The hash of the batch jetton transfer message.
        """
        messages = []
        jetton_master_address = None
        jetton_wallet_address = None

        for data in data_list:
            if jetton_master_address is None or jetton_master_address != data.jetton_master_address:
                jetton_wallet_address = await Jetton(self.client).get_jetton_wallet_address(
                    jetton_master_address=data.jetton_master_address.to_str(),
                    owner_address=self.address.to_str(),
                )
                jetton_master_address = data.jetton_master_address
                jetton_wallet_address = jetton_wallet_address

            messages.append(
                self.create_wallet_internal_message(
                    destination=jetton_wallet_address,
                    value=amount_to_nano(data.amount),
                    body=Jetton.build_transfer_body(
                        recipient_address=data.destination,
                        response_address=self.address,
                        jetton_amount=amount_to_nano(data.jetton_amount),
                        forward_payload=data.forward_payload,
                        forward_amount=amount_to_nano(data.forward_amount),
                    ),
                )
            )

        message_hash = await self._raw_transfer(messages=messages)

        return message_hash

    async def build_encrypted_comment_body(self, text: str, destination: Union[Address, str]) -> Cell:
        """
        Build an encrypted comment body.

        :param text: The comment text to encrypt.
        :param destination: The destination address for the encrypted comment.
        :return: The encrypted comment cell.
        """
        if isinstance(destination, str):
            destination = Address(destination)

        their_key = await self.get_public_key(address=destination)

        return create_encrypted_comment_cell(
            text=text,
            sender_address=self.address,
            our_private_key=self.private_key,
            their_public_key=their_key,
        )
