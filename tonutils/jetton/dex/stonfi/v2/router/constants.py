from dataclasses import dataclass

from tonutils.utils import to_nano

TX_DEADLINE = 15 * 60


@dataclass
class RouterAddresses:
    MAINNET = "EQDQ6j53q21HuZtw6oclm7z4LU2cG6S2OKvpSSMH548d7kJT"  # noqa
    TESTNET = "kQALh-JBBIKK7gr0o4AVf9JZnEsFndqO0qTCyT-D-yBsWk0v"  # noqa


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
