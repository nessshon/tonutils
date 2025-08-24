from dataclasses import dataclass

from tonutils.utils import to_nano


@dataclass
class PTONAddresses:
    MAINNET = "0:671963027f7f85659ab55b821671688601cdcf1ee674fc7fbbb1a776a18d34a3"  # noqa
    TESTNET = "0:024b7d03368510ecd7c0a4fbf387b78199267d2f8ca027e964356b5b6bc4d04f"  # noqa


@dataclass
class GasConstants:
    TON_TRANSFER = to_nano(0.01)
    DEPLOY_WALLET = to_nano(0.1)


@dataclass
class OpCodes:
    TON_TRANSFER = 0x01f3835d
    DEPLOY_WALLET = 0x4f5f4313
