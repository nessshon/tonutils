from __future__ import annotations

from typing import Tuple, List, Union

from ._base import Wallet
from ..data import WalletV3Data
from ...client import Client


class WalletV3R1(Wallet):
    """
    A class representing Wallet V3 R1 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c724101010100620000c0ff0020dd2082014c97ba9730ed44d0d70b1fe0a4f2608308d71820d31fd31fd31ff82313bbf263ed44d0d31fd31fd3ffd15132baf2a15144baf2a204f901541055f910f2a3f8009320d74a96d307d402fb00e8d101a4c8cb1fcb1fcbffc9ed543fbe6ee0"  # noqa

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> WalletV3R1:
        return super().from_private_key(client, private_key, wallet_id=wallet_id, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV3R1, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id=wallet_id, **kwargs)

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV3R1, bytes, bytes, List[str]]:
        return super().create(client, wallet_id=wallet_id, **kwargs)

    @classmethod
    def create_data(cls, public_key: bytes, wallet_id: int = 698983191, seqno: int = 0) -> WalletV3Data:
        return WalletV3Data(public_key, wallet_id, seqno)


class WalletV3R2(Wallet):
    """
    A class representing Wallet V3 R2 in the TON blockchain.
    """

    CODE_HEX = "b5ee9c724101010100710000deff0020dd2082014c97ba218201339cbab19f71b0ed44d0d31fd31f31d70bffe304e0a4f2608308d71820d31fd31fd31ff82313bbf263ed44d0d31fd31fd3ffd15132baf2a15144baf2a204f901541055f910f2a3f8009320d74a96d307d402fb00e8d101a4c8cb1fcb1fcbffc9ed5410bd6dad"  # noqa

    @classmethod
    def from_private_key(
            cls,
            client: Client,
            private_key: bytes,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> WalletV3R2:
        return super().from_private_key(client, private_key, wallet_id=wallet_id, **kwargs)

    @classmethod
    def from_mnemonic(
            cls,
            client: Client,
            mnemonic: Union[List[str], str],
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV3R2, bytes, bytes, List[str]]:
        return super().from_mnemonic(client, mnemonic, wallet_id=wallet_id, **kwargs)

    @classmethod
    def create(
            cls,
            client: Client,
            wallet_id: int = 698983191,
            **kwargs,
    ) -> Tuple[WalletV3R2, bytes, bytes, List[str]]:
        return super().create(client, wallet_id=wallet_id, **kwargs)

    @classmethod
    def create_data(
            cls,
            public_key: bytes,
            wallet_id: int = 698983191,
            seqno: int = 0,
    ) -> WalletV3Data:
        return WalletV3Data(public_key, wallet_id, seqno)
