from enum import Enum
from typing import Callable, Literal

from pytoniq_core.crypto.keys import words


class NetworkGlobalID(int, Enum):
    MAINNET = -239
    TESTNET = -3


def generate_wallet_id(
        subwallet_id: int = 0,
        workchain: int = 0,
        wallet_version: int = 0,
        network_global_id: Literal[NetworkGlobalID.TESTNET, NetworkGlobalID.MAINNET] = NetworkGlobalID.MAINNET,
) -> int:
    """
    Generates a wallet_id according to the TON V5 specification.

    :param subwallet_id: Subwallet counter (uint15), usually 0
    :param workchain: Workchain ID (int8), e.g., 0 or -1
    :param wallet_version: Wallet version (uint8), for V5R1 usually 0
    :param network_global_id: Global network ID (e.g., -239 for mainnet, -3 for testnet)
    :return: wallet_id as int32 (TON spec)
    """
    if subwallet_id > 0x7FFF:
        raise ValueError("subwallet_id must fit in 15 bits (0..32767)")

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
            f"Invalid mnemonic length: {mnemonic_length}. Valid lengths: {valid_lengths}"

        invalid_words = [(i, w) for i, w in enumerate(mnemonic, start=1) if w not in words]

        if invalid_words:
            invalid_words_str = ", ".join(f"{index}. {word}" for index, word in invalid_words)
            raise ValueError(f"Invalid mnemonic words: {invalid_words_str}")

        return func(cls, client, mnemonic, *args, **kwargs)

    return wrapper
