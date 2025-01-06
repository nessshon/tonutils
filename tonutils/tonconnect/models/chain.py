from enum import Enum


class CHAIN(str, Enum):
    """
    Represents the available chains (networks) for TonConnect.
    Each value is a string used as an identifier for the Ton blockchain network.
    """
    mainnet = "-239"
    testnet = "-3"
