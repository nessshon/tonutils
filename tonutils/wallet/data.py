from __future__ import annotations

from pytoniq_core import Builder, Cell, Slice, TlbScheme, begin_cell


class WalletV2Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_bytes(self.public_key)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV3Data:
        raise NotImplementedError


class WalletV3Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.seqno = seqno

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV3Data:
        raise NotImplementedError


class WalletV4Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno
        self.wallet_id = wallet_id

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .store_bool(False)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV4Data:
        raise NotImplementedError


class WalletV5Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 0,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno
        self.wallet_id = wallet_id

    def serialize(self) -> Cell:
        return (
            Builder()
            .store_uint(1, 1)
            .store_uint(self.seqno, 32)
            .store_uint(self.wallet_id, 32)
            .store_bytes(self.public_key)
            .store_bool(False)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> WalletV5Data:
        raise NotImplementedError


class HighloadWalletV2Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            last_cleaned: int = 0,
    ) -> None:
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.last_cleaned = last_cleaned

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(self.wallet_id, 32)
            .store_uint(self.last_cleaned, 64)
            .store_bytes(self.public_key)
            .store_uint(0, 1)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> HighloadWalletV2Data:
        raise NotImplementedError


class HighloadWalletV3Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            wallet_id: int = 698983191,
            timeout: int = 60 * 5,
            last_cleaned: int = 0,
    ) -> None:
        self.public_key = public_key
        self.wallet_id = wallet_id
        self.timeout = timeout
        self.last_cleaned = last_cleaned

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_bytes(self.public_key)
            .store_uint(self.wallet_id, 32)
            .store_uint(self.last_cleaned, 64)
            .store_uint(0, 1)
            .store_uint(0, 1)
            .store_uint(self.timeout, 22)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> HighloadWalletV2Data:
        raise NotImplementedError


class PreprocessedWalletV2Data(TlbScheme):

    def __init__(
            self,
            public_key: bytes,
            seqno: int = 0,
    ) -> None:
        self.public_key = public_key
        self.seqno = seqno

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_bytes(self.public_key)
            .store_uint(self.seqno, 16)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> PreprocessedWalletV2Data:
        raise NotImplementedError
