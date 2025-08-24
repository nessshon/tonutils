from dataclasses import dataclass

from tonutils.utils import to_nano


@dataclass
class PTONAddresses:
    MAINNET = "0:8cdc1d7640ad5ee326527fc1ad0514f468b30dc84b0173f0e155f451b4e11f7c"  # noqa
    TESTNET = "0:1c3af5d29e73a109d2d873aba9d84098c2d34d4f39663a589d05e0ace5c14f57"  # noqa


@dataclass
class GasConstants:
    DEPLOY_WALLET = to_nano(1.05)


@dataclass
class OpCodes:
    DEPLOY_WALLET = 0x6cc43573
