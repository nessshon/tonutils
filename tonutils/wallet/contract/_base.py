from __future__ import annotations

import time
from typing import Any, Optional, List, Union, Tuple

from nacl.signing import SigningKey
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
    private_key_to_public_key,
)
from pytoniq_core.crypto.signature import sign_message

from ..messages import TransferMessageType
from ..op_codes import *
from ..utils import validate_mnemonic
from ...client import Client
from ...contract import Contract
from ...dns.utils import resolve_wallet_address
from ...utils import (
    create_encrypted_comment_cell,
    normalize_hash,
    to_nano,
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
            wallet_id: int = 698983191,
            **kwargs,
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

        if len(private_key) == 32:
            private_key += public_key

        self.private_key = private_key
        self.wallet_id = wallet_id

        self._data = self.create_data(public_key, wallet_id=wallet_id, **kwargs).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(cls, *args, **kwargs) -> Any:
        """
        Create wallet data.

        :param kwargs: Additional arguments.
        :return: Wallet data instance.
        """
        raise NotImplementedError

    async def _create_deploy_msg(self) -> MessageAny:
        """
        Create a deployment message for the wallet.
        """
        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=[],
            seqno=0,
        )

        return self.create_external_msg(
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

        :param private_key: The private key to sign the message.
        :param messages: The list of wallet messages.
        :param kwargs: Additional optional parameters:
            - seqno: The sequence number. Defaults to 0.
            - wallet_id: The wallet ID. Defaults to 698983191.
            - valid_until: The validity timestamp. Defaults to None.
            - op_code: The operation code. Defaults to None.
        :return: The serialized message cell.
        """
        assert len(messages) <= 4, "For common wallet, maximum messages amount is 4"

        seqno = kwargs.get("seqno", None)
        wallet_id = kwargs.get("wallet_id", self.wallet_id)
        valid_until = kwargs.get("valid_until", None)
        op_code = kwargs.get("op_code", None)

        signing_message = begin_cell().store_uint(wallet_id, 32)

        if seqno == 0:
            signing_message.store_bits("1" * 32)
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
            send_mode: int = 3,
            value: int = 0,
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
                .store_uint(TEXT_COMMENT_OPCODE, 32)
                .store_snake_string(body)
                .end_cell()
            )

        message = cls.create_internal_msg(
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
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            **kwargs,
    ) -> Any:
        """
        Create a wallet from a private key.

        :param client: The client to interact with the blockchain. Defaults to None.
        :param private_key: The private key.
        :return: A wallet instance.
        """
        if len(private_key) == 32:
            signing_key = SigningKey(private_key)
            private_key += signing_key.verify_key.encode()

        public_key = private_key_to_public_key(private_key)
        return cls(client, public_key, private_key, **kwargs)

    @classmethod
    @validate_mnemonic
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            **kwargs,
    ) -> Tuple[Any, bytes, bytes, List[str]]:
        """
        Create a wallet from a mnemonic phrase.

        :param client: The client to interact with the blockchain. Defaults to None.
        :param mnemonic: The mnemonic phrase.
        :return: A tuple containing the wallet instance, public key, private key, and mnemonic phrase.
        """
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.split(" ")

        public_key, private_key = mnemonic_to_private_key(mnemonic)
        return cls(client, public_key, private_key, **kwargs), public_key, private_key, mnemonic

    @classmethod
    def create(
            cls,
            client: Client,
            **kwargs,
    ) -> Tuple[Any, bytes, bytes, List[str]]:
        """
        Create a new wallet.

        :param client: The client to interact with the blockchain. Defaults to None.
        :return: A tuple containing the wallet instance, public key, private key, and mnemonic phrase.
        """
        mnemonic = mnemonic_new(24)
        return cls.from_mnemonic(client, mnemonic, **kwargs)

    async def deploy(self) -> str:
        """
        Deploy the wallet to the blockchain.
        """
        message = await self._create_deploy_msg()
        message_boc = message.serialize().to_boc()
        await self.client.send_message(message_boc.hex())

        return normalize_hash(message).hex()

    async def balance(self) -> float:
        """
        Retrieve the current balance of the wallet.

        :return: Wallet balance in TON.
        """
        return await self.get_balance(self.client, self.address)

    @classmethod
    async def get_seqno(
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> int:
        """
        Get the sequence number (seqno) of the wallet.

        :param client: The client to interact with the blockchain.
        :param address: Address object, address string, or a .ton/.t.me domain.
        :return: The sequence number (seqno) of the wallet.
        """
        address = await resolve_wallet_address(client, address)
        method_result = await client.run_get_method(
            address=address.to_str(),
            method_name="seqno",
        )
        return method_result[0]

    @classmethod
    async def get_public_key(
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> int:
        """
        Get the public key of the wallet.

        :param client: The client to interact with the blockchain.
        :param address: Address object, address string, or a .ton/.t.me domain.
        :return: The public key of the wallet.
        """
        address = await resolve_wallet_address(client, address)
        method_result = await client.run_get_method(
            address=address.to_str(),
            method_name="get_public_key",
        )
        return method_result[0]

    async def raw_transfer(
            self,
            messages: Optional[List[WalletMessage]] = None,
            **kwargs,
    ) -> str:
        """
        Perform a raw transfer operation.

        :param messages: The list of wallet messages to transfer.
        :return: The hash of the transfer message.
        """
        if messages is None:
            messages = []

        seqno = kwargs.get("seqno", None)
        if seqno is None:
            try:
                kwargs["seqno"] = seqno = await self.get_seqno(self.client, self.address)
            except (Exception,):
                kwargs["seqno"] = seqno = 0

        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=messages or [],
            **kwargs,
        )
        state_init = self.state_init if seqno == 0 else None
        message = self.create_external_msg(dest=self.address, body=body, state_init=state_init)
        message_boc = message.serialize().to_boc()
        await self.client.send_message(message_boc.hex())

        return normalize_hash(message).hex()

    async def transfer(
            self,
            destination: Union[Address, str],
            amount: Union[int, float] = 0,
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
            **kwargs,
    ) -> str:
        """
        Transfer funds to a destination address.

        :param destination: Address object, address string, or a .ton/.t.me domain.
        :param amount: The amount to transfer. Defaults to 0.
        :param body: The body of the message. Defaults to an empty cell.
            If a string is provided, it will be used as a transaction comment.
        :param state_init: The state initialization. Defaults to None.
        :param kwargs: Additional arguments.
        :return: The hash of the transfer message.
        """
        destination = await resolve_wallet_address(self.client, destination)
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
            **kwargs,
        )

        return message_hash

    async def transfer_message(self, message: TransferMessageType, **kwargs) -> str:
        """
        Transfer a single message built from a TransferMessageType instance.

        This method builds the provided TransferMessageType into a WalletMessage
        and sends it to the blockchain.

        :param message: An instance of TransferMessageType containing the transfer details.
        :param kwargs: Additional arguments for raw_transfer (e.g., seqno, valid_until).
        :return: The hash of the transfer message.
        """
        message = await message.build(self)
        return await self.raw_transfer(messages=[message], **kwargs)

    async def batch_transfer_messages(self, messages: List[TransferMessageType], **kwargs) -> str:
        """
        Transfer multiple messages in a single transaction.

        This method builds each TransferMessageType into a WalletMessage and sends
        them together in a batch operation to the blockchain.

        :param messages: A list of TransferMessageType instances containing transfer details.
        :param kwargs: Additional arguments for raw_transfer (e.g., seqno, valid_until).
        :return: The hash of the batch transfer message.
        """
        messages = [await message.build(self) for message in messages]
        return await self.raw_transfer(messages=messages, **kwargs)

    async def build_encrypted_comment_body(self, text: str, destination: Union[Address, str]) -> Cell:
        """
        Build an encrypted comment body.

        :param text: The comment text to encrypt.
        :param destination: Address object, address string, or a .ton/.t.me domain.
        :return: The encrypted comment cell.
        """
        destination = await resolve_wallet_address(self.client, destination)
        their_key = await self.get_public_key(self.client, destination)

        return create_encrypted_comment_cell(
            text=text,
            sender_address=self.address,
            our_private_key=self.private_key,
            their_public_key=their_key,
        )
