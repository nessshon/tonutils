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
    MAINNET = "0:5f0564fb5f604783db57031ce1cf668a88d4d4d6da6de4db222b4b920d6fd800"  # noqa
    TESTNET = "0:c770fc6508e48dfecf95970e776c5a626cdc8aa591d5eb11e1c460004ffdb59c"  # noqa


@dataclass
class NativeVaultAddresses:
    MAINNET = "0:dae153a74d894bbc32748198cd626e4f5df4a69ad2fa56ce80fc2644b5708d20"  # noqa
    TESTNET = "0:ec850da7ca17b3665791765653d76a6fae3fdc629f571a67118188ab03bd435a"  # noqa


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
