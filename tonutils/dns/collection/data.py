from __future__ import annotations

from typing import Union

from pytoniq_core import Address, Cell, TlbScheme, begin_cell

from .content import DNSCollectionContent
from ...nft.royalty_params import RoyaltyParams


class DNSCollectionData(TlbScheme):

    def __init__(
            self,
            owner_address: Union[Address, str],
            content: DNSCollectionContent,
            item_code: Cell,
            royalty_params: RoyaltyParams,
            domain: str,
    ) -> None:
        self.owner_address = owner_address
        self.content = content
        self.item_code = item_code
        self.royalty_params = royalty_params
        self.domain = domain

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_address(self.owner_address)
            .store_ref(self.content.serialize())
            .store_ref(self.item_code)
            .store_ref(self.royalty_params.serialize())
            .store_ref(begin_cell().store_string(self.domain).end_cell())
            .end_cell()
        )

    @classmethod
    def deserialize(cls) -> DNSCollectionData:
        raise NotImplementedError
