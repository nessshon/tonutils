import typing as t

from pytoniq_core import Cell, begin_cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike, DNSCategory


async def get_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """
    Get domain name from a DNS contract.

    :param client: TON client for blockchain interactions
    :param address: DNS contract address
    :return: Cell containing the domain name
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_domain",
    )
    return t.cast(Cell, r[0])


class GetDomainGetMethod(ContractProtocol):
    """Mixin providing get_domain() get method for DNS contracts."""

    async def get_domain(self) -> Cell:
        """
        Get domain name from this DNS contract.

        :return: Cell containing the domain name
        """
        return await get_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_auction_info_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get auction information from a DNS contract.

    :param client: TON client for blockchain interactions
    :param address: DNS contract address
    :return: List containing auction details (max_bid, max_bid_address, auction_end_time)
    """
    return await client.run_get_method(
        address=address,
        method_name="get_auction_info",
    )


class GetAuctionInfoGetMethod(ContractProtocol):
    """Mixin providing get_auction_info() get method for DNS contracts."""

    async def get_auction_info(self) -> t.List[t.Any]:
        """
        Get auction information from this DNS contract.

        Returns auction details including max bid, bidder address, and end time.

        :return: List containing auction details (max_bid, max_bid_address, auction_end_time)
        """
        return await get_auction_info_get_method(
            client=self.client,
            address=self.address,
        )


async def get_last_fill_up_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """
    Get last fill-up timestamp from a DNS contract.

    :param client: TON client for blockchain interactions
    :param address: DNS contract address
    :return: Unix timestamp of last fill-up operation
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_last_fill_up_time",
    )
    return int(r[0])


class GetLastFillUpTimeGetMethod(ContractProtocol):
    """Mixin providing get_last_fill_up_time() get method for DNS contracts."""

    async def get_last_fill_up_time(self) -> int:
        """
        Get last fill-up timestamp from this DNS contract.

        Returns when the domain was last renewed or filled up.

        :return: Unix timestamp of last fill-up operation
        """
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
    """
    Resolve DNS record for a specific category and subdomain.

    :param client: TON client for blockchain interactions
    :param address: DNS contract address
    :param category: DNS category to resolve (e.g., wallet, site, storage)
    :param subdomain: Subdomain to resolve (optional, defaults to root)
    :return: Tuple of (resolved_bits, result_cell) where resolved_bits indicates resolution depth
    """
    subdomain = "\x00" if subdomain is None else subdomain
    subdomain_cell = begin_cell().store_snake_string(subdomain).end_cell()

    res = await client.run_get_method(
        address=address,
        method_name="dnsresolve",
        stack=[subdomain_cell.to_slice(), category],
    )
    return int(res[0]), t.cast(Cell, res[1])


class DNSResolveGetMethod(ContractProtocol):
    """Mixin providing dnsresolve() get method for DNS contracts."""

    async def dnsresolve(
        self,
        category: DNSCategory,
        subdomain: t.Optional[str] = None,
    ) -> t.Tuple[int, Cell]:
        """
        Resolve DNS record for a specific category and subdomain.

        :param category: DNS category to resolve (e.g., wallet, site, storage)
        :param subdomain: Subdomain to resolve (optional, defaults to root)
        :return: Tuple of (resolved_bits, result_cell) where resolved_bits indicates resolution depth
        """
        return await dnsresolve_get_method(
            client=self.client,
            address=self.address,
            category=category,
            subdomain=subdomain,
        )
