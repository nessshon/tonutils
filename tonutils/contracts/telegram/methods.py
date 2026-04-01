import typing as t

from ton_core import AddressLike, Cell

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.protocol import ContractProtocol


async def get_full_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """Call ``get_full_domain`` on a Telegram item contract.

    :param client: TON client.
    :param address: Telegram item contract address.
    :return: ``Cell`` containing the full domain name.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_full_domain",
    )
    return t.cast("Cell", r[0])


class GetFullDomainGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_full_domain`` get-method."""

    async def get_full_domain(self) -> Cell:
        """Return full domain name ``Cell``."""
        return await get_full_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_token_name_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """Call ``get_telemint_token_name`` on a Telegram item contract.

    :param client: TON client.
    :param address: Telegram item contract address.
    :return: ``Cell`` containing the token name.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_telemint_token_name",
    )
    return t.cast("Cell", r[0])


class GetTelemintTokenNameGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_telemint_token_name`` get-method."""

    async def get_telemint_token_name(self) -> Cell:
        """Return token name ``Cell``."""
        return await get_telemint_token_name_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_auction_state_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> list[t.Any]:
    """Call ``get_telemint_auction_state`` on a Telegram item contract.

    :param client: TON client.
    :param address: Telegram item contract address.
    :return: Auction state data (last bid, min bid, end time).
    """
    return await client.run_get_method(
        address=address,
        method_name="get_telemint_auction_state",
    )


class GetTelemintAuctionStateGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_telemint_auction_state`` get-method."""

    async def get_telemint_auction_state(self) -> list[t.Any]:
        """Return current auction state data."""
        return await get_telemint_auction_state_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_auction_config_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> list[t.Any]:
    """Call ``get_telemint_auction_config`` on a Telegram item contract.

    :param client: TON client.
    :param address: Telegram item contract address.
    :return: Auction configuration data.
    """
    return await client.run_get_method(
        address=address,
        method_name="get_telemint_auction_config",
    )


class GetTelemintAuctionConfigGetMethod(ContractProtocol[t.Any]):
    """Mixin providing the ``get_telemint_auction_config`` get-method."""

    async def get_telemint_auction_config(self) -> list[t.Any]:
        """Return auction configuration data."""
        return await get_telemint_auction_config_get_method(
            client=self.client,
            address=self.address,
        )
