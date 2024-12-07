from __future__ import annotations

from typing import Any, Dict, List, Optional

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell

from tonutils.utils import serialize_onchain_dict


class BaseOffchainContent(TlbScheme):

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
    def deserialize(cls, cell_slice: Slice) -> BaseOffchainContent:
        raise NotImplementedError


class CollectionOffchainContent(BaseOffchainContent):

    def __init__(self, uri: str, prefix_uri: str) -> None:
        super().__init__(uri)
        self.prefix_uri = prefix_uri

    def serialize(self) -> Cell:
        common_content_cell = (
            begin_cell()
            .store_snake_string(self.prefix_uri)
            .end_cell()
        )
        return (
            begin_cell()
            .store_ref(super().serialize())
            .store_ref(common_content_cell)
            .end_cell()
        )


class NFTOffchainContent(BaseOffchainContent):

    def __init__(self, suffix_uri: str) -> None:
        super().__init__(suffix_uri)

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_snake_string(self.uri)
            .end_cell()
        )


class CollectionModifiedOffchainContent(BaseOffchainContent):

    def __init__(self, uri: str) -> None:
        super().__init__(uri)


class NFTModifiedOffchainContent(BaseOffchainContent):

    def __init__(self, uri: str) -> None:
        super().__init__(uri)


class BaseOnchainContent(TlbScheme):

    def __init__(self, **kwargs) -> None:
        for key, val in kwargs.items():
            setattr(self, key, val)

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(0x00, 8)
            .store_dict(serialize_onchain_dict(self.__dict__))
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> BaseOnchainContent:
        raise NotImplementedError


class CollectionModifiedOnchainContent(BaseOnchainContent):

    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            image: Optional[str] = None,
            image_data: Optional[bytes] = None,
            cover_image: Optional[str] = None,
            cover_image_data: Optional[bytes] = None,
            **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            image=image,
            image_data=image_data,
            cover_image=cover_image,
            cover_image_data=cover_image_data,
            **kwargs,
        )


class NFTModifiedOnchainContent(BaseOnchainContent):

    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            image: Optional[str] = None,
            image_data: Optional[bytes] = None,
            buttons: Optional[List[Dict[str, Any]]] = None,
            attributes: Optional[List[Dict[str, Any]]] = None,
            **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            image=image,
            image_data=image_data,
            buttons=buttons,
            attributes=attributes,
            **kwargs,
        )
