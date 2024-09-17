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

    def __init__(self, uri: str) -> None:
        super().__init__(uri)


class NFTOffchainContent(BaseOffchainContent):

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


class CollectionOnchainContent(BaseOnchainContent):

    def __init__(
            self,
            name: str,
            description: Optional[str] = None,
            image: Optional[str] = None,
            image_data: Optional[bytes] = None,
            cover_image: Optional[str] = None,
            cover_image_data: Optional[bytes] = None,
            social_links: Optional[List[str]] = None,
            **kwargs,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            image=image,
            image_data=image_data,
            cover_image=cover_image,
            cover_image_data=cover_image_data,
            social_links=social_links,
            **kwargs,
        )


class NFTOnchainContent(BaseOnchainContent):

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
