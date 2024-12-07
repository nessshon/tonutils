from dataclasses import dataclass

from tonutils.utils import to_nano


@dataclass
class PTONAddresses:
    MAINNET = "EQBnGWMCf3-FZZq1W4IWcWiGAc3PHuZ0_H-7sad2oY00o83S"  # noqa
    TESTNET = "kQACS30DNoUQ7NfApPvzh7eBmSZ9L4ygJ-lkNWtba8TQT-Px"  # noqa


@dataclass
class GasConstants:
    TON_TRANSFER = to_nano(0.01)
    DEPLOY_WALLET = to_nano(0.1)


@dataclass
class OpCodes:
    TON_TRANSFER = 0x01f3835d
    DEPLOY_WALLET = 0x4f5f4313
