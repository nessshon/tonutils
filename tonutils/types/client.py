from enum import Enum


class ClientType(str, Enum):
    TONAPI = "tonapi"
    TONCENTER = "toncenter"
    LITESERVER = "liteserver"
