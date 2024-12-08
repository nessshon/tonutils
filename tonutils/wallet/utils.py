from enum import Enum
from typing import Callable

from pytoniq_core.crypto.keys import words


class NetworkGlobalID(int, Enum):
    MAINNET = -239
    TESTNET = -3


def generate_wallet_id(
        subwallet_id: int,
        workchain: int = 0,
        wallet_version: int = 0,
        network_global_id: int = NetworkGlobalID.MAINNET,
) -> int:
    """
    Generates a wallet ID based on global ID, workchain, wallet version, and wallet id.

    :param subwallet_id: The subwallet ID (16-bit unsigned integer).
    :param workchain: The workchain value (8-bit signed integer).
    :param wallet_version: The wallet version (8-bit unsigned integer).
    :param network_global_id: The network global ID (32-bit signed integer).
    """
    ctx = 0
    ctx |= 1 << 31
    ctx |= (workchain & 0xFF) << 23
    ctx |= (wallet_version & 0xFF) << 15
    ctx |= (subwallet_id & 0xFFFF)

    return ctx ^ (network_global_id & 0xFFFFFFFF)


def validate_mnemonic(func: Callable) -> Callable:
    def wrapper(cls, client, mnemonic, *args, **kwargs):
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.split()

        valid_lengths, mnemonic_length = (12, 18, 24), len(mnemonic)

        assert mnemonic_length in valid_lengths, \
            f'Invalid mnemonic length: {mnemonic_length}. Valid lengths: {valid_lengths}'

        invalid_words = [(i, w) for i, w in enumerate(mnemonic, start=1) if w not in words]

        if invalid_words:
            invalid_words_str = ", ".join(f'{index}. {word}' for index, word in invalid_words)
            raise ValueError(f"Invalid mnemonic words: {invalid_words_str}")

        return func(cls, client, mnemonic, *args, **kwargs)

    return wrapper
