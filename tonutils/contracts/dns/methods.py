import typing as t

from pytoniq_core import Cell, begin_cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike, DNSCategory


async def get_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    r = await client.run_get_method(
        address=address,
        method_name="get_domain",
    )
    return t.cast(Cell, r[0])


class GetDomainGetMethod(ContractProtocol):
    async def get_domain(self) -> Cell:
        return await get_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_auction_info_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_auction_info",
    )


class GetAuctionInfoGetMethod(ContractProtocol):
    async def get_auction_info(self) -> t.List[t.Any]:
        return await get_auction_info_get_method(
            client=self.client,
            address=self.address,
        )


async def get_last_fill_up_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    r = await client.run_get_method(
        address=address,
        method_name="get_last_fill_up_time",
    )
    return int(r[0])


class GetLastFillUpTimeGetMethod(ContractProtocol):
    async def get_last_fill_up_time(self) -> int:
        return await get_last_fill_up_time_get_method(
            client=self.client,
            address=self.address,
        )


async def dnsresolve_get_method(
    client: ClientProtocol,
    address: AddressLike,
    category: DNSCategory,
    subdomain: t.Optional[str] = None,
) -> t.Tuple[int, Cell]:
    subdomain = "\x00" if subdomain is None else subdomain
    subdomain_cell = begin_cell().store_snake_string(subdomain).end_cell()

    res = await client.run_get_method(
        address=address,
        method_name="dnsresolve",
        stack=[subdomain_cell.to_slice(), category],
    )
    return int(res[0]), t.cast(Cell, res[1])


class DNSResolveGetMethod(ContractProtocol):
    async def dnsresolve(
        self,
        category: DNSCategory,
        subdomain: t.Optional[str] = None,
    ) -> t.Tuple[int, Cell]:
        return await dnsresolve_get_method(
            client=self.client,
            address=self.address,
            category=category,
            subdomain=subdomain,
        )
