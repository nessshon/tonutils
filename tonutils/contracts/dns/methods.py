import typing as t

from ton_core import AddressLike, Cell, DNSCategory, begin_cell

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.protocol import ContractProtocol


async def get_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """Call ``get_domain`` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :return: Domain name ``Cell``.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_domain",
    )
    return t.cast("Cell", r[0])


class GetDomainGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_domain`` get-method."""

    async def get_domain(self) -> Cell:
        """Return domain name ``Cell``."""
        return await get_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_auction_info_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> list[t.Any]:
    """Call ``get_auction_info`` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :return: List of [max_bid, max_bid_address, auction_end_time].
    """
    return await client.run_get_method(
        address=address,
        method_name="get_auction_info",
    )


class GetAuctionInfoGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_auction_info`` get-method."""

    async def get_auction_info(self) -> list[t.Any]:
        """Return auction info (max bid, bidder, end time)."""
        return await get_auction_info_get_method(
            client=self.client,
            address=self.address,
        )


async def get_last_fill_up_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call ``get_last_fill_up_time`` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :return: Last fill-up unix timestamp.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_last_fill_up_time",
    )
    return int(r[0])


class GetLastFillUpTimeGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_last_fill_up_time`` get-method."""

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
    subdomain: str | None = None,
) -> tuple[int, Cell]:
    """Call ``dnsresolve`` on a DNS contract.

    :param client: TON client.
    :param address: DNS contract address.
    :param category: DNS category to resolve.
    :param subdomain: Subdomain to resolve, or ``None`` for root.
    :return: Tuple of (resolved_bits, result ``Cell``).
    """
    subdomain = "\x00" if subdomain is None else subdomain
    subdomain_cell = begin_cell().store_snake_string(subdomain).end_cell()

    res = await client.run_get_method(
        address=address,
        method_name="dnsresolve",
        stack=[subdomain_cell.to_slice(), category],
    )
    return int(res[0]), t.cast("Cell", res[1])


class DNSResolveGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``dnsresolve`` get-method."""

    async def dnsresolve(
        self,
        category: DNSCategory,
        subdomain: str | None = None,
    ) -> tuple[int, Cell]:
        """Resolve a DNS record.

        :param category: DNS category to resolve.
        :param subdomain: Subdomain to resolve, or ``None`` for root.
        :return: Tuple of (resolved_bits, result ``Cell``).
        """
        return await dnsresolve_get_method(
            client=self.client,
            address=self.address,
            category=category,
            subdomain=subdomain,
        )
