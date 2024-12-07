from dataclasses import dataclass

from tonutils.utils import to_nano

TX_DEADLINE = 60 * 5


@dataclass
class OpCodes:
    SWAP_NATIVE = 0xea06185d
    SWAP_JETTON = 0xe3a0d482
    CREATE_VAULT = 0x21cfe02b


@dataclass
class FactoryAddresses:
    MAINNET = "EQBfBWT7X2BHg9tXAxzhz2aKiNTU1tpt5NsiK0uSDW_YAJ67"  # noqa
    TESTNET = "kQDHcPxlCOSN_s-Vlw53bFpibNyKpZHV6xHhxGAAT_21nJre"  # noqa


@dataclass
class NativeVaultAddresses:
    MAINNET = "EQDa4VOnTYlLvDJ0gZjNYm5PXfSmmtL6Vs6A_CZEtXCNICq_"  # noqa
    TESTNET = "kQDshQ2nyhezZleRdlZT12pvrj_cYp9XGmcRgYirA71DWlOb"  # noqa


@dataclass
class SwapJettonToJettonConstants:
    GAS_AMOUNT = to_nano(0.3)
    FORWARD_GAS_AMOUNT = to_nano(0.25)


@dataclass
class SwapJettonToTONConstants:
    GAS_AMOUNT = to_nano(0.3)
    FORWARD_GAS_AMOUNT = to_nano(0.25)


@dataclass
class SwapTONToJettonConstants:
    FORWARD_GAS_AMOUNT = to_nano(0.25)


@dataclass
class GasConstants:
    swap_jetton_to_jetton = SwapJettonToJettonConstants
    swap_jetton_to_ton = SwapJettonToTONConstants
    swap_ton_to_jetton = SwapTONToJettonConstants
