import typing as t

from pytoniq_core import Cell, begin_cell

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.protocol import ContractProtocol
from tonutils.types import AddressLike, DNSCategory


async def get_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """Call `get_domain` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :return: Domain name `Cell`.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_domain",
    )
    return t.cast(Cell, r[0])


class GetDomainGetMethod(ContractProtocol):
    """Mixin for the `get_domain` get-method."""

    async def get_domain(self) -> Cell:
        """Return domain name `Cell`."""
        return await get_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_auction_info_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """Call `get_auction_info` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :return: List of [max_bid, max_bid_address, auction_end_time].
    """
    return await client.run_get_method(
        address=address,
        method_name="get_auction_info",
    )


class GetAuctionInfoGetMethod(ContractProtocol):
    """Mixin for the `get_auction_info` get-method."""

    async def get_auction_info(self) -> t.List[t.Any]:
        """Return auction info (max bid, bidder, end time)."""
        return await get_auction_info_get_method(
            client=self.client,
            address=self.address,
        )


async def get_last_fill_up_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call `get_last_fill_up_time` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :return: Last fill-up unix timestamp.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_last_fill_up_time",
    )
    return int(r[0])


class GetLastFillUpTimeGetMethod(ContractProtocol):
    """Mixin for the `get_last_fill_up_time` get-method."""

    async def get_last_fill_up_time(self) -> int:
        """Return last fill-up unix timestamp."""
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
    """Call `dnsresolve` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :param category: DNS category to resolve.
    :param subdomain: Subdomain to resolve, or `None` for root.
    :return: Tuple of (resolved_bits, result `Cell`).
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
    """Mixin for the `dnsresolve` get-method."""

    async def dnsresolve(
        self,
        category: DNSCategory,
        subdomain: t.Optional[str] = None,
    ) -> t.Tuple[int, Cell]:
        """Resolve a DNS record.

        :param category: DNS category to resolve.
        :param subdomain: Subdomain to resolve, or `None` for root.
        :return: Tuple of (resolved_bits, result `Cell`).
        """
        return await dnsresolve_get_method(
            client=self.client,
            address=self.address,
            category=category,
            subdomain=subdomain,
        )
