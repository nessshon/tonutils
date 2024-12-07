from dataclasses import dataclass

from tonutils.utils import to_nano


@dataclass
class RouterAddresses:
    MAINNET = "EQB3ncyBUTjZUA5EnFKR5_EnOMI9V1tTEAAPaiU71gc4TiUt"  # noqa
    TESTNET = "kQBsGx9ArADUrREB34W-ghgsCgBShvfUr4Jvlu-0KGc33a1n"  # noqa


@dataclass
class OpCodes:
    SWAP = 0x25938561


@dataclass
class SwapJettonToJettonConstants:
    GAS_AMOUNT = to_nano(0.22)
    FORWARD_GAS_AMOUNT = to_nano(0.175)


@dataclass
class SwapJettonToTONConstants:
    GAS_AMOUNT = to_nano(0.17)
    FORWARD_GAS_AMOUNT = to_nano(0.125)


@dataclass
class SwapTONToJettonConstants:
    FORWARD_GAS_AMOUNT = to_nano(0.185)


@dataclass
class GasConstants:
    swap_jetton_to_jetton = SwapJettonToJettonConstants
    swap_jetton_to_ton = SwapJettonToTONConstants
    swap_ton_to_jetton = SwapTONToJettonConstants
