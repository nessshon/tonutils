from dataclasses import dataclass

from tonutils.utils import to_nano

TX_DEADLINE = 15 * 60


@dataclass
class RouterAddresses:
    MAINNET = "0:d0ea3e77ab6d47b99b70ea87259bbcf82d4d9c1ba4b638abe9492307e78f1dee"  # noqa
    TESTNET = "0:0b87e24104828aee0af4a380157fd2599c4b059dda8ed2a4c2c93f83fb206c5a"  # noqa


@dataclass
class OpCodes:
    SWAP = 0x6664de2a
    CROSS_SWAP = 0x69cf1a5b


@dataclass
class SwapJettonToJettonConstants:
    GAS_AMOUNT = to_nano(0.3)
    FORWARD_GAS_AMOUNT = to_nano(0.24)


@dataclass
class SwapJettonToTONConstants:
    GAS_AMOUNT = to_nano(0.3)
    FORWARD_GAS_AMOUNT = to_nano(0.24)


@dataclass
class SwapTONToJettonConstants:
    FORWARD_GAS_AMOUNT = to_nano(0.3)


@dataclass
class GasConstants:
    swap_jetton_to_jetton = SwapJettonToJettonConstants
    swap_jetton_to_ton = SwapJettonToTONConstants
    swap_ton_to_jetton = SwapTONToJettonConstants
