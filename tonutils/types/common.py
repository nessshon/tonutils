from __future__ import annotations

import typing as t
from decimal import Decimal
from enum import Enum

from pytoniq_core import Address


class SendMode(int, Enum):
    CARRY_ALL_REMAINING_BALANCE = 128
    CARRY_ALL_REMAINING_INCOMING_VALUE = 64
    DESTROY_ACCOUNT_IF_ZERO = 32
    BOUNCE_IF_ACTION_FAIL = 16
    IGNORE_ERRORS = 2
    PAY_GAS_SEPARATELY = 1
    DEFAULT = 0


class NetworkGlobalID(int, Enum):
    MAINNET = -239
    TESTNET = -3


class WorkchainID(int, Enum):
    BASECHAIN = 0
    MASTERCHAIN = -1


class MetadataPrefix(int, Enum):
    ONCHAIN = 0x00
    OFFCHAIN = 0x01


DEFAULT_SUBWALLET_ID = 698983191
DEFAULT_SENDMODE = SendMode.PAY_GAS_SEPARATELY | SendMode.IGNORE_ERRORS

AddressLike = t.Union[Address, str]
NumberLike = t.Union[int, float, str, Decimal]
