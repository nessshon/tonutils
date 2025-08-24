from dataclasses import dataclass

from tonutils.utils import to_nano


@dataclass
class RouterAddresses:
    MAINNET = "0:779dcc815138d9500e449c5291e7f12738c23d575b5310000f6a253bd607384e"  # noqa
    TESTNET = "0:6c1b1f40ac00d4ad1101df85be82182c0a005286f7d4af826f96efb4286737dd"  # noqa


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
