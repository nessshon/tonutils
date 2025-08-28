import typing as t
from dataclasses import dataclass
from enum import Enum

from pytoniq_core import Cell, StateInit

from ..utils.converters import to_cell


class ContractState(str, Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    UNINIT = "uninit"
    NONEXIST = "nonexist"


@dataclass
class ContractStateInfo:
    code_raw: t.Optional[str] = None
    data_raw: t.Optional[str] = None

    balance: int = 0
    state: ContractState = ContractState.NONEXIST
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None

    @property
    def code(self) -> t.Optional[Cell]:
        return to_cell(self.code_raw) if self.code_raw else None

    @property
    def data(self) -> t.Optional[Cell]:
        return to_cell(self.data_raw) if self.data_raw else None

    @property
    def state_init(self) -> StateInit:
        return StateInit(code=self.code, data=self.data)

    def __repr__(self) -> str:
        parts = " ".join(f"{k}: {v!r}" for k, v in vars(self).items())
        return f"< {self.__class__.__name__} {parts} >"


class BaseContractVersion(str, Enum): ...


class WalletVersion(BaseContractVersion):
    WalletV1R1 = "wallet_v1r1"
    WalletV1R2 = "wallet_v1r2"
    WalletV1R3 = "wallet_v1r3"
    WalletV2R1 = "wallet_v2r1"
    WalletV2R2 = "wallet_v2r2"
    WalletV3R1 = "wallet_v3r1"
    WalletV3R2 = "wallet_v3r2"
    WalletV4R1 = "wallet_v4r1"
    WalletV4R2 = "wallet_v4r2"
    WalletV5Beta = "wallet_v5_beta"
    WalletV5R1 = "wallet_v5r1"

    WalletHighloadV2 = "wallet_highloadv_v2"
    WalletHighloadV3R1 = "wallet_highload_v3r1"

    WalletPreprocessedV2 = "wallet_preprocessed_v2"


class NFTCollectionVersion(BaseContractVersion):
    NFTCollectionStandard = "nft_collection_standard"
    NFTCollectionEditable = "nft_collection_editable"


class NFTItemVersion(BaseContractVersion):
    NFTItemStandard = "nft_item_standard"
    NFTItemEditable = "nft_item_editable"
    NFTItemSoulbound = "nft_item_soulbound"


class NFTItemSingleVersion(BaseContractVersion):
    NFTItemEditableSingle = "nft_item_editable_single"
    NFTItemSoulboundSingle = "nft_item_soulbound_single"
