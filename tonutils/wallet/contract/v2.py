from __future__ import annotations

import time
from typing import Tuple, List, Union

from pytoniq_core import begin_cell, WalletMessage, Cell
from pytoniq_core.crypto.signature import sign_message

from ._base import Wallet
from ..data import WalletV2Data
from ...client import Client


class WalletV2Base(Wallet):

    def __init__(
            self,
            client: Client,
            public_key: bytes,
            private_key: bytes,
            **kwargs,
    ) -> None:
        super().__init__(client, public_key, private_key, **kwargs)

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            **kwargs,
    ) -> WalletV2Base:
        return super().from_private_key(client, private_key, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            **kwargs,
    ) -> Tuple[WalletV2Base, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, **kwargs)

    @classmethod
    def create(
            cls,
            client: Client,
            **kwargs,
    ) -> Tuple[WalletV2Base, bytes, bytes, List[str]]:
        return super().create(client, **kwargs)

    @classmethod
    def create_data(cls, public_key: bytes, seqno: int = 0, **kwargs) -> WalletV2Data:
        return WalletV2Data(public_key, seqno)

    def raw_create_transfer_msg(
            self,
            private_key: bytes,
            messages: List[WalletMessage],
            **kwargs,
    ) -> Cell:
        assert len(messages) <= 1, 'For wallet v2, message amount must be 1'

        seqno = kwargs.get("seqno", None)
        valid_until = kwargs.get("valid_until", None)

        signing_message = begin_cell().store_uint(seqno, 32)
        if seqno == 0:
            signing_message.store_bits('1' * 32)
        else:
            if valid_until is not None:
                signing_message.store_uint(valid_until, 32)
            else:
                signing_message.store_uint(int(time.time()) + 60, 32)
        if len(messages) == 0:
            signing_message.store_uint(0, 32)
        else:
            signing_message.store_cell(messages[0].serialize())

        signing_message = signing_message.end_cell()
        signature = sign_message(signing_message.hash, private_key)

        return (
            begin_cell()
            .store_bytes(signature)
            .store_cell(signing_message)
            .end_cell()
        )


class WalletV2R1(WalletV2Base):
    CODE_HEX = "b5ee9c724101010100570000aaff0020dd2082014c97ba9730ed44d0d70b1fe0a4f2608308d71820d31fd31f01f823bbf263ed44d0d31fd3ffd15131baf2a103f901541042f910f2a2f800029320d74a96d307d402fb00e8d1a4c8cb1fcbffc9ed54a1370bb6"  # noqa


class WalletV2R2(WalletV2Base):
    CODE_HEX = "b5ee9c724101010100630000c2ff0020dd2082014c97ba218201339cbab19c71b0ed44d0d31fd70bffe304e0a4f2608308d71820d31fd31f01f823bbf263ed44d0d31fd3ffd15131baf2a103f901541042f910f2a2f800029320d74a96d307d402fb00e8d1a4c8cb1fcbffc9ed54044cd7a1"  # noqa
