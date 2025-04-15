from __future__ import annotations

from typing import Union

from pytoniq_core import Address, Cell, TlbScheme, begin_cell

from .content import SubdomainCollectionContent
from ...nft.royalty_params import RoyaltyParams


class FullDomain(TlbScheme):

    def __init__(
            self,
            domain: str,
            tld: str,
    ) -> None:
        self.domain = domain
        self.tld = tld

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_ref(begin_cell().store_string(self.tld).end_cell())
            .store_ref(begin_cell().store_string(self.domain).end_cell())
            .end_cell()
        )

    @classmethod
    def deserialize(cls) -> SubdomainCollectionData:
        raise NotImplementedError


class SubdomainCollectionData(TlbScheme):

    def __init__(
            self,
            owner_address: Union[Address, str],
            content: SubdomainCollectionContent,
            item_code: Cell,
            royalty_params: RoyaltyParams,
            full_domain: FullDomain,
    ) -> None:
        self.owner_address = owner_address
        self.content = content
        self.item_code = item_code
        self.royalty_params = royalty_params
        self.full_domain = full_domain

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_address(self.owner_address)
            .store_ref(self.content.serialize())
            .store_ref(self.item_code)
            .store_ref(self.royalty_params.serialize())
            .store_ref(self.full_domain.serialize())
            .end_cell()
        )

    @classmethod
    def deserialize(cls) -> SubdomainCollectionData:
        raise NotImplementedError
