from __future__ import annotations

import abc
import typing as t

from pytoniq_core import (
    Cell,
    Slice,
    begin_cell,
    Builder,
)

from ...types.common import (
    DEFAULT_SUBWALLET_ID,
    NetworkGlobalID,
    WorkchainID,
)
from ...types.keystructs import PublicKey
from ...types.tlb.contract import BaseContractData
from ...utils.wallet_utils import WalletV5SubwalletID


class BaseWalletData(BaseContractData, abc.ABC):

    def __init__(self, public_key: PublicKey) -> None:
        super().__init__()
        self.public_key = public_key


class WalletV1Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
    ) -> None:
        super().__init__(public_key)
        self.seqno = seqno

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_bytes(self.public_key.bytes)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV1Data:
        return cls(
            seqno=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
        )


class WalletV2Data(WalletV1Data): ...


class WalletV3Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
    ) -> None:
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_bytes(self.public_key.bytes)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV3Data:
        return cls(
            seqno=cs.load_uint(32),
            subwallet_id=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
        )


class WalletV4Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        plugins: t.Optional[Cell] = None,
    ) -> None:
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_bytes(self.public_key.bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV4Data:
        return cls(
            seqno=cs.load_uint(32),
            subwallet_id=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletV5BetaData(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: WalletV5SubwalletID,
        seqno: int = 0,
        plugins: t.Optional[Cell] = None,
    ) -> None:
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins

    def _store_wallet_id(self, builder: Builder) -> None:
        builder.store_int(self.subwallet_id.network_global_id, 32)
        builder.store_int(self.subwallet_id.workchain, 8)
        builder.store_uint(self.subwallet_id.version, 8)
        builder.store_uint(self.subwallet_id.subwallet_number, 32)

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.seqno, 33)
        self._store_wallet_id(cell)
        cell.store_bytes(self.public_key.bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def _load_wallet_id(cls, cs: Slice) -> WalletV5SubwalletID:
        return WalletV5SubwalletID(
            network_global_id=NetworkGlobalID(cs.load_int(32)),
            workchain=WorkchainID(cs.load_int(8)),
            version=cs.load_uint(8),
            subwallet_number=cs.load_uint(32),
        )

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV5BetaData:
        return cls(
            seqno=cs.load_uint(33),
            subwallet_id=cls._load_wallet_id(cs),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletV5Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: WalletV5SubwalletID,
        seqno: int = 0,
        plugins: t.Optional[Cell] = None,
        is_signature_allowed: bool = True,
    ) -> None:
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins
        self.is_signature_allowed = is_signature_allowed

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_bool(self.is_signature_allowed)
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id.pack(), 32)
        cell.store_bytes(self.public_key.bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, network_global_id: NetworkGlobalID) -> WalletV5Data:
        is_signature_allowed = cs.load_bool()
        seqno = cs.load_uint(32)
        subwallet_id = cs.load_uint(32)
        subwallet_id = WalletV5SubwalletID.unpack(subwallet_id, network_global_id)
        public_key = PublicKey(cs.load_bytes(32))
        plugins = cs.load_maybe_ref()
        return cls(
            is_signature_allowed=is_signature_allowed,
            seqno=seqno,
            subwallet_id=subwallet_id,
            public_key=public_key,
            plugins=plugins,
        )


class WalletHighloadV2Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        last_cleaned: int = 0,
        old_queries: t.Optional[Cell] = None,
    ) -> None:
        super().__init__(public_key)
        self.subwallet_id = subwallet_id
        self.last_cleaned = last_cleaned
        self.old_queries = old_queries

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.subwallet_id, 32)
        cell.store_uint(self.last_cleaned, 64)
        cell.store_bytes(self.public_key.bytes)
        cell.store_dict(self.old_queries)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletHighloadV2Data:
        return cls(
            subwallet_id=cs.load_uint(32),
            last_cleaned=cs.load_uint(64),
            public_key=PublicKey(cs.load_bytes(32)),
            old_queries=cs.load_maybe_ref(),
        )


class WalletHighloadV3Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        old_queries: t.Optional[Cell] = None,
        queries: t.Optional[Cell] = None,
        last_clean_time: int = 0,
        timeout: int = 60 * 5,
    ) -> None:
        super().__init__(public_key)
        self.subwallet_id = subwallet_id
        self.old_queries = old_queries
        self.queries = queries
        self.last_clean_time = last_clean_time
        self.timeout = timeout

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_bytes(self.public_key.bytes)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_dict(self.old_queries)
        cell.store_dict(self.queries)
        cell.store_uint(self.last_clean_time, 64)
        cell.store_uint(self.timeout, 22)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletHighloadV3Data:
        return cls(
            public_key=PublicKey(cs.load_bytes(32)),
            subwallet_id=cs.load_uint(32),
            old_queries=cs.load_maybe_ref(),
            queries=cs.load_maybe_ref(),
            last_clean_time=cs.load_uint(64),
            timeout=cs.load_uint(22),
        )


class WalletPreprocessedV2Data(BaseWalletData):

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
    ) -> None:
        super().__init__(public_key)
        self.seqno = seqno

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_bytes(self.public_key.bytes)
        cell.store_uint(self.seqno, 16)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletPreprocessedV2Data:
        return cls(
            public_key=PublicKey(cs.load_bytes(32)),
            seqno=cs.load_uint(16),
        )
