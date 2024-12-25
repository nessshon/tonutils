from __future__ import annotations

import time
from typing import Any, Dict, Optional, List, Union, Tuple

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

from ..data import (
    TransferData,
    TransferNFTData,
    TransferJettonData,
    SwapTONToJettonData,
    SwapJettonToTONData,
    SwapJettonToJettonData,
)
from ..op_codes import *
from ..utils import validate_mnemonic
from ...client import (
    Client,
    LiteserverClient,
    TonapiClient,
    ToncenterClient,
)
from ...contract import Contract
from ...exceptions import UnknownClientError
from ...jetton import JettonMaster, JettonWallet
from ...jetton.dex.dedust import Factory
from ...jetton.dex.stonfi import StonfiRouterV1, StonfiRouterV2
from ...nft import NFTStandard
from ...utils import (
    create_encrypted_comment_cell,
    message_to_boc_hex,
    to_nano, to_amount,
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
        assert len(messages) <= 4, 'For common wallet, maximum messages amount is 4'

        seqno = kwargs.get("seqno", None)
        wallet_id = kwargs.get("wallet_id", self.wallet_id)
        valid_until = kwargs.get("valid_until", None)
        op_code = kwargs.get("op_code", None)

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
        message_boc_hex, message_hash = message_to_boc_hex(message)
        await self.client.send_message(message_boc_hex)

        return message_hash

    async def balance(self) -> int:
        """
        Retrieve the current balance of the wallet.

        :return: The balance of the wallet as an integer.
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
        """
        if isinstance(address, Address):
            address = address.to_str()

        method_result = await client.run_get_method(
            address=address,
            method_name="seqno",
        )

        if isinstance(client, TonapiClient):
            seqno = int(method_result["decoded"]["state"] or 0)
        elif isinstance(client, ToncenterClient):
            seqno = int(method_result["stack"][0]["value"], 16)
        elif isinstance(client, LiteserverClient):
            seqno = int(method_result[0])
        else:
            raise UnknownClientError(client.__class__.__name__)

        return seqno

    @classmethod
    async def get_public_key(
            cls,
            client: Client,
            address: Union[Address, str],
    ) -> int:
        """
        Get the public key of the wallet.
        """
        if isinstance(address, Address):
            address = address.to_str()

        method_result = await client.run_get_method(
            address=address,
            method_name="get_public_key",
        )

        if isinstance(client, TonapiClient):
            public_key = int(method_result["decoded"]["public_key"] or 0)
        elif isinstance(client, ToncenterClient):
            public_key = int(method_result["stack"][0]["value"], 16)
        elif isinstance(client, LiteserverClient):
            public_key = int(method_result[0])
        else:
            raise UnknownClientError(client.__class__.__name__)

        return public_key

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
                kwargs["seqno"] = await self.get_seqno(self.client, self.address)
            except (Exception,):
                kwargs["seqno"] = seqno = 0

        body = self.raw_create_transfer_msg(
            private_key=self.private_key,
            messages=messages or [],
            **kwargs,
        )
        state_init = self.state_init if seqno == 0 else None
        message = self.create_external_msg(dest=self.address, body=body, state_init=state_init)
        message_boc_hex, message_hash = message_to_boc_hex(message)

        await self.client.send_message(message_boc_hex)
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

        their_key = await self.get_public_key(self.client, destination)

        return create_encrypted_comment_cell(
            text=text,
            sender_address=self.address,
            our_private_key=self.private_key,
            their_public_key=their_key,
        )

    async def transfer(
            self,
            destination: Union[Address, str],
            amount: Union[int, float] = 0,
            body: Optional[Union[Cell, str]] = None,
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
        )

        return message_hash

    async def batch_transfer(self, data_list: List[TransferData], **kwargs) -> str:
        """
        Perform a batch transfer operation.

        :param data_list: The list of transfer data.
        :return: The hash of the batch transfer message.
        """
        messages = [
            self.create_wallet_internal_message(
                destination=data.destination,
                value=to_nano(data.amount),
                body=data.body,
                state_init=data.state_init,
                **data.other,
            ) for data in data_list
        ]

        message_hash = await self.raw_transfer(messages=messages, **kwargs)

        return message_hash

    async def transfer_nft(
            self,
            destination: Union[Address, str],
            nft_address: Union[Address, str],
            response_address: Optional[Union[Address, str]] = None,
            forward_payload: Optional[Union[Cell, str]] = None,
            forward_amount: Union[int, float] = 0.001,
            amount: Union[int, float] = 0.05,
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
        :return: The hash of the NFT transfer message.
        """
        if isinstance(destination, str):
            destination = Address(destination)
        if isinstance(nft_address, str):
            nft_address = Address(nft_address)

        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(TEXT_COMMENT_OPCODE, 32)
                .store_string(forward_payload)
                .end_cell()
            )

        message_hash = await self.transfer(
            destination=nft_address,
            amount=amount,
            body=NFTStandard.build_transfer_body(
                new_owner_address=destination,
                response_address=response_address or destination,
                forward_payload=forward_payload,
                forward_amount=to_nano(forward_amount),
            ),
            **kwargs,
        )

        return message_hash

    async def batch_nft_transfer(self, data_list: List[TransferNFTData], **kwargs) -> str:
        """
        Perform a batch NFT transfer operation.

        :param data_list: The list of NFT transfer data.
        :return: The hash of the batch NFT transfer message.
        """
        messages = [
            self.create_wallet_internal_message(
                destination=data.nft_address,
                value=to_nano(data.amount),
                body=NFTStandard.build_transfer_body(
                    new_owner_address=data.destination,
                    response_address=data.response_address,
                    forward_payload=data.forward_payload,
                    forward_amount=to_nano(data.forward_amount),

                ),
                **data.other,
            ) for data in data_list
        ]

        message_hash = await self.raw_transfer(messages=messages, **kwargs)

        return message_hash

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
        :return: The hash of the jetton transfer message.
        """
        if isinstance(destination, str):
            destination = Address(destination)
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(forward_payload, str):
            forward_payload = (
                begin_cell()
                .store_uint(TEXT_COMMENT_OPCODE, 32)
                .store_snake_string(forward_payload)
                .end_cell()
            )

        jetton_wallet_address = await JettonMaster.get_wallet_address(
            client=self.client,
            owner_address=self.address.to_str(),
            jetton_master_address=jetton_master_address,
        )

        message_hash = await self.transfer(
            destination=jetton_wallet_address,
            amount=amount,
            body=JettonWallet.build_transfer_body(
                recipient_address=destination,
                response_address=self.address,
                jetton_amount=int(jetton_amount * (10 ** jetton_decimals)),
                forward_payload=forward_payload,
                forward_amount=to_nano(forward_amount),
            ),
            **kwargs,
        )

        return message_hash

    async def batch_jetton_transfer(self, data_list: List[TransferJettonData], **kwargs) -> str:
        """
        Perform a batch jetton transfer operation.

        :param data_list: The list of jetton transfer data.
        :return: The hash of the batch jetton transfer message.
        """
        messages = []
        wallets: Dict[str, Address] = {}

        for data in data_list:
            if data.jetton_wallet_address is None:
                jetton_wallet_address = wallets.get(data.jetton_master_address.to_str(), None)

                if jetton_wallet_address is None:
                    jetton_wallet_address = await JettonMaster.get_wallet_address(
                        client=self.client,
                        owner_address=self.address.to_str(),
                        jetton_master_address=data.jetton_master_address,
                    )
                    wallets[data.jetton_master_address.to_str()] = jetton_wallet_address

                data.jetton_wallet_address = jetton_wallet_address

            messages.append(
                self.create_wallet_internal_message(
                    destination=data.jetton_wallet_address,
                    value=to_nano(data.amount),
                    body=JettonWallet.build_transfer_body(
                        recipient_address=data.destination,
                        response_address=self.address,
                        jetton_amount=int(data.jetton_amount * (10 ** data.jetton_decimals)),
                        forward_payload=data.forward_payload,
                        forward_amount=to_nano(data.forward_amount),
                    ),
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages, **kwargs)

        return message_hash

    async def dedust_swap_ton_to_jetton(
            self,
            jetton_master_address: Union[Address, str],
            ton_amount: Union[int, float],
            min_amount: Union[int, float] = 0,
            jetton_decimals: int = 9,
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> str:
        """
        Perform a swap operation.

        :param jetton_master_address: The jetton master address to swap to.
        :param ton_amount: The amount of TON to swap.
        :param min_amount: The minimum amount of Jetton to receive. Defaults to 0.
        :param jetton_decimals: Jetton decimal precision used to convert min_amount to nano units.
        :param factory_address: The factory address.
        :param native_vault_address: The native vault address.
        :return: The hash of the swap message.

        https://docs.dedust.io/docs/introduction
        """
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(factory_address, str):
            factory_address = Address(factory_address)

        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        factory = Factory(self.client, factory_address, native_vault_address)

        to, value, body = await factory.get_swap_ton_to_jetton_tx_params(
            recipient_address=self.address,
            offer_jetton_address=jetton_master_address,
            offer_amount=to_nano(ton_amount),
            min_ask_amount=to_nano(min_amount, jetton_decimals),
        )
        message_hash = await self.transfer(
            destination=to,
            amount=to_amount(value),
            body=body,
            bounce=True,
            **kwargs,
        )

        return message_hash

    async def batch_dedust_swap_ton_to_jetton(
            self,
            data_list: List[SwapTONToJettonData],
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
    ) -> str:
        """
        Perform a batch swap operation.

        :param data_list: The list of swap data.
        :param factory_address: The factory address.
        :param native_vault_address: The native vault address.
        :return: The hash of the batch swap message.

        https://docs.dedust.io/docs/introduction
        """
        if isinstance(factory_address, str):
            factory_address = Address(factory_address)

        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        messages = []

        for data in data_list:
            factory = Factory(self.client, factory_address, native_vault_address)

            to, value, body = await factory.get_swap_ton_to_jetton_tx_params(
                recipient_address=self.address,
                offer_jetton_address=data.jetton_master_address,
                offer_amount=to_nano(data.ton_amount),
                min_ask_amount=to_nano(data.min_amount, data.jetton_decimals),
            )
            messages.append(
                self.create_wallet_internal_message(
                    destination=to,
                    value=value,
                    body=body,
                    bounce=True,
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages)

        return message_hash

    async def dedust_swap_jetton_to_ton(
            self,
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            min_amount: Union[int, float] = 0,
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> str:
        """
        Perform a swap operation.

        :param jetton_master_address: The jetton master address to swap from.
        :param jetton_amount: The amount of jetton to swap.
        :param jetton_decimals: The jetton decimals.
        :param min_amount: The minimum amount of TON to receive. Defaults to 0.
        :param factory_address: The factory address.
        :param native_vault_address: The native vault address.
        :return: The hash of the swap message.

        https://docs.dedust.io/docs/introduction
        """
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(factory_address, str):
            factory_address = Address(factory_address)

        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        factory = Factory(self.client, factory_address, native_vault_address)

        to, value, body = await factory.get_swap_jetton_to_ton_tx_params(
            recipient_address=self.address,
            offer_jetton_address=jetton_master_address,
            offer_amount=to_nano(jetton_amount, jetton_decimals),
            min_ask_amount=to_nano(min_amount),
        )

        message_hash = await self.transfer(
            destination=to,
            amount=to_amount(value),
            body=body,
            bounce=True,
            **kwargs,
        )

        return message_hash

    async def batch_dedust_swap_jetton_to_ton(
            self,
            data_list: List[SwapJettonToTONData],
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
    ) -> str:
        """
        Perform a batch swap jetton to ton operation.

        :param data_list: The list of swap jetton to ton data.
        :param factory_address: The factory address.
        :param native_vault_address: The native vault address.
        :return: The hash of the batch swap jetton to ton message.

        https://docs.dedust.io/docs/introduction
        """
        if isinstance(factory_address, str):
            factory_address = Address(factory_address)

        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        messages = []

        for data in data_list:
            factory = Factory(self.client, factory_address, native_vault_address)

            to, value, body = await factory.get_swap_jetton_to_ton_tx_params(
                recipient_address=self.address,
                offer_jetton_address=data.jetton_master_address,
                offer_amount=to_nano(data.jetton_amount, data.jetton_decimals),
                min_ask_amount=to_nano(data.min_amount),
            )
            messages.append(
                self.create_wallet_internal_message(
                    destination=to,
                    value=value,
                    body=body,
                    bounce=True,
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages)

        return message_hash

    async def dedust_swap_jetton_to_jetton(
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
    ) -> str:
        """
        Perform a swap operation.

        :param from_jetton_master_address: The jetton master address to swap from.
        :param to_jetton_master_address: The jetton master address to swap to.
        :param jetton_amount: The amount of jetton to swap.
        :param from_jetton_decimals: The jetton decimals of the from_jetton_master_address (used for calculating jetton_amount).
        :param to_jetton_decimals: The jetton decimals of the to_jetton_master_address (used for calculating min_amount).
        :param min_amount: The minimum amount of jetton to receive. Defaults to 0.
        :param factory_address: The factory address.
        :param native_vault_address: The native vault address.
        :return: The hash of the swap message.

        https://docs.dedust.io/docs/introduction
        """
        if isinstance(from_jetton_master_address, str):
            from_jetton_master_address = Address(from_jetton_master_address)

        if isinstance(to_jetton_master_address, str):
            to_jetton_master_address = Address(to_jetton_master_address)

        if isinstance(factory_address, str):
            factory_address = Address(factory_address)

        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        factory = Factory(self.client, factory_address, native_vault_address)

        to, value, body = await factory.get_swap_jetton_to_jetton_tx_params(
            recipient_address=self.address,
            offer_jetton_address=from_jetton_master_address,
            ask_jetton_address=to_jetton_master_address,
            offer_amount=to_nano(jetton_amount, from_jetton_decimals),
            min_ask_amount=to_nano(min_amount, to_jetton_decimals),
        )

        message_hash = await self.transfer(
            destination=to,
            amount=to_amount(value),
            body=body,
            bounce=True,
            **kwargs,
        )

        return message_hash

    async def batch_dedust_swap_jetton_to_jetton(
            self,
            data_list: List[SwapJettonToJettonData],
            factory_address: Optional[Union[Address, str]] = None,
            native_vault_address: Optional[Union[Address, str]] = None,
    ) -> str:
        """
        Perform a batch swap jetton to jetton operation.

        :param data_list: The list of swap jetton to jetton data.
        :param factory_address: The factory address.
        :param native_vault_address: The native vault address.
        :return: The hash of the batch swap jetton to jetton message.

        https://docs.dedust.io/docs/introduction
        """
        if isinstance(factory_address, str):
            factory_address = Address(factory_address)

        if isinstance(native_vault_address, str):
            native_vault_address = Address(native_vault_address)

        messages = []

        for data in data_list:
            factory = Factory(self.client, factory_address, native_vault_address)

            to, value, body = await factory.get_swap_jetton_to_jetton_tx_params(
                recipient_address=self.address,
                offer_jetton_address=data.from_jetton_master_address,
                ask_jetton_address=data.to_jetton_master_address,
                offer_amount=to_nano(data.jetton_amount, data.from_jetton_decimals),
                min_ask_amount=to_nano(data.min_amount, data.to_jetton_decimals),
            )

            messages.append(
                self.create_wallet_internal_message(
                    destination=to,
                    value=value,
                    body=body,
                    bounce=True,
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages)

        return message_hash

    async def stonfi_swap_ton_to_jetton(
            self,
            jetton_master_address: Union[Address, str],
            ton_amount: Union[int, float],
            min_amount: Union[int, float] = 0,
            jetton_decimals: int = 9,
            version: int = 2,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> str:
        """
        Perform a swap TON to jetton operation.

        :param jetton_master_address: The jetton master address to swap to.
        :param ton_amount: The amount of TON to swap.
        :param min_amount: The minimum amount of jetton to receive. Defaults to 0.
        :param jetton_decimals: Jetton decimal precision used to convert min_amount to nano units.
        :param version: The version of the STONfi Router. Defaults to 2.
        :param router_address: The STONfi Router address.
        :param pton_address: The pTON address.
        :return: The hash of the swap message.

        https://docs.ston.fi/docs/developer-section/architecture
        """
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(router_address, str):
            router_address = Address(router_address)

        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        if version == 1:
            router_v1 = StonfiRouterV1(self.client, router_address, pton_address)

            to, value, body = await router_v1.get_swap_ton_to_jetton_tx_params(
                user_wallet_address=self.address,
                ask_jetton_address=jetton_master_address,
                offer_amount=to_nano(ton_amount),
                min_ask_amount=to_nano(min_amount, jetton_decimals),
            )
        elif version == 2:
            router_v2 = StonfiRouterV2(self.client, router_address, pton_address)

            to, value, body = await router_v2.get_swap_ton_to_jetton_tx_params(
                user_wallet_address=self.address,
                receiver_address=self.address,
                offer_jetton_address=jetton_master_address,
                offer_amount=to_nano(ton_amount),
                min_ask_amount=to_nano(min_amount, jetton_decimals),
                refund_address=self.address,
            )
        else:
            raise ValueError(f"Unsupported STONfi Router version: {version}")

        message_hash = await self.transfer(
            destination=to,
            amount=to_amount(value),
            body=body,
            bounce=True,
            **kwargs,
        )

        return message_hash

    async def batch_stonfi_swap_ton_to_jetton(
            self,
            data_list: List[SwapTONToJettonData],
            version: int = 2,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
    ) -> str:
        """
        Perform a batch swap operation.

        :param data_list: The list of swap data.
        :param version: The version of the STONfi Router. Defaults to 2.
        :param router_address: The STONfi Router address.
        :param pton_address: The pTON address.
        :return: The hash of the batch swap message.

        https://docs.ston.fi/docs/developer-section/architecture
        """
        if isinstance(router_address, str):
            router_address = Address(router_address)

        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        messages = []

        for data in data_list:
            if version == 1:
                router_v1 = StonfiRouterV1(self.client, router_address, pton_address)

                to, value, body = await router_v1.get_swap_ton_to_jetton_tx_params(
                    user_wallet_address=self.address,
                    ask_jetton_address=data.jetton_master_address,
                    offer_amount=to_nano(data.ton_amount),
                    min_ask_amount=to_nano(data.min_amount, data.jetton_decimals),
                )
            elif version == 2:
                router_v2 = StonfiRouterV2(self.client, router_address, pton_address)

                to, value, body = await router_v2.get_swap_ton_to_jetton_tx_params(
                    user_wallet_address=self.address,
                    receiver_address=self.address,
                    offer_jetton_address=data.jetton_master_address,
                    offer_amount=to_nano(data.ton_amount),
                    min_ask_amount=to_nano(data.min_amount, data.jetton_decimals),
                    refund_address=self.address,
                )
            else:
                raise ValueError(f"Unsupported STONfi Router version: {version}")

            messages.append(
                self.create_wallet_internal_message(
                    destination=to,
                    value=value,
                    body=body,
                    bounce=True,
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages)

        return message_hash

    async def stonfi_swap_jetton_to_ton(
            self,
            jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            min_amount: Union[int, float] = 0,
            version: int = 2,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> str:
        """
        Perform a swap jetton to TON operation.

        :param jetton_master_address: The jetton master address to swap from.
        :param jetton_amount: The amount of jetton to swap.
        :param jetton_decimals: The jetton decimals. Defaults to 9.
        :param min_amount: The minimum amount of TON to receive. Defaults to 0.
        :param version: The version of the STONfi Router. Defaults to 2.
        :param router_address: The STONfi Router address.
        :param pton_address: The pTON address.
        :return: The hash of the swap message.

        https://docs.ston.fi/docs/developer-section/architecture
        """
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(router_address, str):
            router_address = Address(router_address)

        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        if version == 1:
            router_v1 = StonfiRouterV1(self.client, router_address, pton_address)

            to, value, body = await router_v1.get_swap_jetton_to_ton_tx_params(
                offer_jetton_address=jetton_master_address,
                user_wallet_address=self.address,
                offer_amount=to_nano(jetton_amount, jetton_decimals),
                min_ask_amount=to_nano(min_amount),
            )
        elif version == 2:
            router_v2 = StonfiRouterV2(self.client, router_address, pton_address)

            to, value, body = await router_v2.get_swap_jetton_to_ton_tx_params(
                offer_jetton_address=jetton_master_address,
                receiver_address=self.address,
                user_wallet_address=self.address,
                offer_amount=to_nano(jetton_amount, jetton_decimals),
                min_ask_amount=to_nano(min_amount),
                refund_address=self.address,
            )
        else:
            raise ValueError(f"Unsupported STONfi Router version: {version}")

        message_hash = await self.transfer(
            destination=to,
            amount=to_amount(value),
            body=body,
            bounce=True,
            **kwargs,
        )

        return message_hash

    async def batch_stonfi_swap_jetton_to_ton(
            self,
            data_list: List[SwapJettonToTONData],
            version: int = 2,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
    ) -> str:
        """
        Perform a batch swap operation.

        :param data_list: The list of swap data.
        :param version: The version of the STONfi Router. Defaults to 2.
        :param router_address: The STONfi Router address.
        :param pton_address: The pTON address.
        :return: The hash of the batch swap message.

        https://docs.ston.fi/docs/developer-section/architecture
        """
        if isinstance(router_address, str):
            router_address = Address(router_address)

        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        messages = []

        for data in data_list:
            if version == 1:
                router_v1 = StonfiRouterV1(self.client, router_address, pton_address)

                to, value, body = await router_v1.get_swap_jetton_to_ton_tx_params(
                    offer_jetton_address=data.jetton_master_address,
                    user_wallet_address=self.address,
                    offer_amount=to_nano(data.jetton_amount, data.jetton_decimals),
                    min_ask_amount=to_nano(data.min_amount),
                )
            elif version == 2:
                router_v2 = StonfiRouterV2(self.client, router_address, pton_address)

                to, value, body = await router_v2.get_swap_jetton_to_ton_tx_params(
                    offer_jetton_address=data.jetton_master_address,
                    receiver_address=self.address,
                    user_wallet_address=self.address,
                    offer_amount=to_nano(data.jetton_amount, data.jetton_decimals),
                    min_ask_amount=to_nano(data.min_amount),
                    refund_address=self.address,
                )
            else:
                raise ValueError(f"Unsupported STONfi Router version: {version}")

            messages.append(
                self.create_wallet_internal_message(
                    destination=to,
                    value=value,
                    body=body,
                    bounce=True,
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages)

        return message_hash

    async def stonfi_swap_jetton_to_jetton(
            self,
            from_jetton_master_address: Union[Address, str],
            to_jetton_master_address: Union[Address, str],
            jetton_amount: Union[int, float],
            jetton_decimals: int = 9,
            min_amount: Union[int, float] = 0,
            version: int = 2,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
            **kwargs,
    ) -> str:
        """
        Perform a swap jetton to jetton operation.

        :param from_jetton_master_address: The jetton master address to swap from.
        :param to_jetton_master_address: The jetton master address to swap to.
        :param jetton_amount: The amount of jetton to swap.
        :param jetton_decimals: The jetton decimals. Defaults to 9.
        :param min_amount: The minimum amount of jetton to receive. Defaults to 0.
        :param version: The version of the STONfi Router. Defaults to 2.
        :param router_address: The STONfi Router address.
        :param pton_address: The pTON address.
        :return: The hash of the swap message.

        https://docs.ston.fi/docs/developer-section/architecture
        """
        if isinstance(from_jetton_master_address, str):
            from_jetton_master_address = Address(from_jetton_master_address)

        if isinstance(to_jetton_master_address, str):
            to_jetton_master_address = Address(to_jetton_master_address)

        if isinstance(router_address, str):
            router_address = Address(router_address)

        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        if version == 1:
            router_v1 = StonfiRouterV1(self.client, router_address, pton_address)

            to, value, body = await router_v1.get_swap_jetton_to_jetton_tx_params(
                user_wallet_address=self.address,
                offer_jetton_address=from_jetton_master_address,
                ask_jetton_address=to_jetton_master_address,
                offer_amount=to_nano(jetton_amount, jetton_decimals),
                min_ask_amount=to_nano(min_amount, jetton_decimals),
            )
        elif version == 2:
            router_v2 = StonfiRouterV2(self.client, router_address, pton_address)

            to, value, body = await router_v2.get_swap_jetton_to_jetton_tx_params(
                user_wallet_address=self.address,
                receiver_address=self.address,
                refund_address=self.address,
                offer_jetton_address=from_jetton_master_address,
                ask_jetton_address=to_jetton_master_address,
                offer_amount=to_nano(jetton_amount, jetton_decimals),
                min_ask_amount=to_nano(min_amount, jetton_decimals),
            )
        else:
            raise ValueError(f"Unsupported STONfi Router version: {version}")

        message_hash = await self.transfer(
            destination=to,
            amount=to_amount(value),
            body=body,
            bounce=True,
            **kwargs,
        )

        return message_hash

    async def batch_stonfi_swap_jetton_to_jetton(
            self,
            data_list: List[SwapJettonToJettonData],
            version: int = 2,
            router_address: Optional[Union[Address, str]] = None,
            pton_address: Optional[Union[Address, str]] = None,
    ) -> str:
        """
        Perform a batch swap operation.

        :param data_list: The list of swap data.
        :param version: The version of the STONfi Router. Defaults to 2.
        :param router_address: The STONfi Router address.
        :param pton_address: The pTON address.
        :return: The hash of the batch swap message.

        https://docs.ston.fi/docs/developer-section/architecture
        """
        if isinstance(router_address, str):
            router_address = Address(router_address)

        if isinstance(pton_address, str):
            pton_address = Address(pton_address)

        messages = []

        for data in data_list:
            if version == 1:
                router_v1 = StonfiRouterV1(self.client, router_address, pton_address)

                to, value, body = await router_v1.get_swap_jetton_to_jetton_tx_params(
                    user_wallet_address=self.address,
                    offer_jetton_address=data.from_jetton_master_address,
                    ask_jetton_address=data.to_jetton_master_address,
                    offer_amount=to_nano(data.jetton_amount, data.from_jetton_decimals),
                    min_ask_amount=to_nano(data.min_amount, data.to_jetton_decimals),
                )
            elif version == 2:
                router_v2 = StonfiRouterV2(self.client, router_address, pton_address)

                to, value, body = await router_v2.get_swap_jetton_to_jetton_tx_params(
                    user_wallet_address=self.address,
                    receiver_address=self.address,
                    refund_address=self.address,
                    offer_jetton_address=data.from_jetton_master_address,
                    ask_jetton_address=data.to_jetton_master_address,
                    offer_amount=to_nano(data.jetton_amount, data.from_jetton_decimals),
                    min_ask_amount=to_nano(data.min_amount, data.to_jetton_decimals),
                )
            else:
                raise ValueError(f"Unsupported STONfi Router version: {version}")

            messages.append(
                self.create_wallet_internal_message(
                    destination=to,
                    value=value,
                    body=body,
                    bounce=True,
                    **data.other,
                )
            )

        message_hash = await self.raw_transfer(messages=messages)

        return message_hash
