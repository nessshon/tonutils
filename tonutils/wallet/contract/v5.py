from __future__ import annotations

import time
from typing import List, Tuple, Union

from pytoniq_core import Cell, WalletMessage, begin_cell
from pytoniq_core.crypto.signature import sign_message

from . import Wallet
from ..data import WalletV5Data
from ..op_codes import *
from ..utils import generate_wallet_id
from ...client import Client


class WalletV5R1(Wallet):
    """
    A class representing Wallet V5 R1 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c7241021401000281000114ff00f4a413f4bcf2c80b01020120020d020148030402dcd020d749c120915b8f6320d70b1f2082106578746ebd21821073696e74bdb0925f03e082106578746eba8eb48020d72101d074d721fa4030fa44f828fa443058bd915be0ed44d0810141d721f4058307f40e6fa1319130e18040d721707fdb3ce03120d749810280b99130e070e2100f020120050c020120060902016e07080019adce76a2684020eb90eb85ffc00019af1df6a2684010eb90eb858fc00201480a0b0017b325fb51341c75c875c2c7e00011b262fb513435c280200019be5f0f6a2684080a0eb90fa02c0102f20e011e20d70b1f82107369676ebaf2e08a7f0f01e68ef0eda2edfb218308d722028308d723208020d721d31fd31fd31fed44d0d200d31f20d31fd3ffd70a000af90140ccf9109a28945f0adb31e1f2c087df02b35007b0f2d0845125baf2e0855036baf2e086f823bbf2d0882292f800de01a47fc8ca00cb1f01cf16c9ed542092f80fde70db3cd81003f6eda2edfb02f404216e926c218e4c0221d73930709421c700b38e2d01d72820761e436c20d749c008f2e09320d74ac002f2e09320d71d06c712c2005230b0f2d089d74cd7393001a4e86c128407bbf2e093d74ac000f2e093ed55e2d20001c000915be0ebd72c08142091709601d72c081c12e25210b1e30f20d74a111213009601fa4001fa44f828fa443058baf2e091ed44d0810141d718f405049d7fc8ca0040048307f453f2e08b8e14038307f45bf2e08c22d70a00216e01b3b0f2d090e2c85003cf1612f400c9ed54007230d72c08248e2d21f2e092d200ed44d0d2005113baf2d08f54503091319c01810140d721d70a00f2e08ee2c8ca0058cf16c9ed5493f2c08de20010935bdb31e1d74cd0b4d6c35e"  # noqa

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            wallet_id: int = 0,
            workchain: int = 0,
            wallet_version: int = 0,
            network_global_id: int = -239,
            **kwargs,
    ) -> None:
        """
        Initialize a Wallet instance.

        :param client: The client to interact with the blockchain.
        :param public_key: The public key of the wallet.
        :param private_key: The private key of the wallet.
        :param wallet_id: The wallet ID (32-bit unsigned integer).
        :param workchain: The workchain value (8-bit signed integer).
        :param wallet_version: The wallet version (8-bit unsigned integer).
        :param network_global_id: The network global ID (32-bit signed integer).
        """
        wallet_id = generate_wallet_id(
            subwallet_id=wallet_id,
            workchain=workchain,
            wallet_version=wallet_version,
            network_global_id=network_global_id,
        )
        super().__init__(client, public_key, private_key, wallet_id, **kwargs)

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 0,
            **kwargs,
    ) -> Tuple[WalletV5R1, bytes, bytes, List[str]]:
        return super().create(client, wallet_id, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 0,
            **kwargs,
    ) -> Tuple[WalletV5R1, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id, **kwargs)

    @classmethod
    def create_data(cls, public_key: bytes, wallet_id: int = 0, seqno: int = 0) -> WalletV5Data:
        return WalletV5Data(public_key, wallet_id, seqno)

    def create_signed_internal_msg(self, messages: List[WalletMessage], seqno: int, **kwargs) -> Cell:
        return self.raw_create_transfer_msg(
            private_key=self.private_key,
            op_code=SIGNED_ITERNAL_OPCODE,
            messages=messages,
            seqno=seqno,
            **kwargs,
        )

    def create_signed_external_msg(self, messages: List[WalletMessage], seqno: int, **kwargs) -> Cell:
        return self.raw_create_transfer_msg(
            private_key=self.private_key,
            op_code=SIGNED_EXTERNAL_OPCODE,
            messages=messages,
            seqno=seqno,
            **kwargs,
        )

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        assert len(messages) <= 255, 'For wallet v5, maximum messages amount is 255'

        seqno = kwargs.get("seqno", None)
        op_code = kwargs.get("op_code", SIGNED_EXTERNAL_OPCODE)
        valid_until = kwargs.get("valid_until", None)
        wallet_id = kwargs.get("wallet_id", self.wallet_id)

        signing_message = begin_cell().store_uint(op_code, 32)
        signing_message.store_uint(wallet_id, 32)

        if seqno == 0:
            signing_message.store_bits('1' * 32)
        else:
            if valid_until is not None:
                signing_message.store_uint(valid_until, 32)
            else:
                signing_message.store_uint(int(time.time()) + 60, 32)

        signing_message.store_uint(seqno, 32)
        signing_message.store_cell(self.pack_actions(messages))

        signing_message = signing_message.end_cell()
        signature = sign_message(signing_message.hash, private_key)

        return (
            begin_cell()
            .store_cell(signing_message)
            .store_bytes(signature)
            .end_cell()
        )

    @staticmethod
    def pack_actions(messages: List[WalletMessage]) -> Cell:
        """
        Packs a list of wallet messages into a single Cell.

        :param messages: A list of WalletMessage instances to pack.
        :return: A Cell containing the packed messages.
        """
        list_cell = Cell.empty()

        for msg in messages:
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

        return (
            begin_cell()
            .store_uint(1, 1)
            .store_ref(list_cell)
            .store_uint(0, 1)
            .end_cell()
        )
