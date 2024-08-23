from __future__ import annotations

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell


class OffchainBaseContent(TlbScheme):

    def __init__(self, uri: str) -> None:
        self.uri = uri

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(0x01, 8)
            .store_snake_string(self.uri)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> OffchainBaseContent:
        raise NotImplementedError


class OffchainCommonContent(TlbScheme):

    def __init__(self, uri: str) -> None:
        self.uri = uri

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_snake_string(self.uri)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> OffchainCommonContent:
        raise NotImplementedError


class OffchainContent(TlbScheme):

    def __init__(self, uri: str, prefix_uri: str) -> None:
        self.uri = uri
        self.prefix_uri = prefix_uri

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_ref(OffchainBaseContent(self.uri).serialize())
            .store_ref(OffchainCommonContent(self.prefix_uri).serialize())
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> OffchainContent:
        raise NotImplementedError
