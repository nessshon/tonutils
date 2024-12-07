from dataclasses import dataclass

from tonutils.utils import to_nano


@dataclass
class PTONAddresses:
    MAINNET = "EQCM3B12QK1e4yZSf8GtBRT0aLMNyEsBc_DhVfRRtOEffLez"  # noqa
    TESTNET = "kQAcOvXSnnOhCdLYc6up2ECYwtNNTzlmOlidBeCs5cFPV7AM"  # noqa


@dataclass
class GasConstants:
    DEPLOY_WALLET = to_nano(1.05)


@dataclass
class OpCodes:
    DEPLOY_WALLET = 0x6cc43573
