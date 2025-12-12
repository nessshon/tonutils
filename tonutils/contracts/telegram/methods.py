import typing as t

from pytoniq_core import Cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike


async def get_full_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """
    Get full domain name from a DNS/Telegram item contract.

    :param client: TON client for blockchain interactions
    :param address: DNS/Telegram item contract address
    :return: Cell containing full domain name
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_full_domain",
    )
    return t.cast(Cell, r[0])


class GetFullDomainGetMethod(ContractProtocol):
    """Mixin providing get_full_domain() get method for DNS/Telegram items."""

    async def get_full_domain(self) -> Cell:
        """
        Get full domain name from this DNS/Telegram item.

        Returns the complete domain string (e.g., "username.t.me").

        :return: Cell containing full domain name
        """
        return await get_full_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_token_name_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    """
    Get token name from a Telegram username/gift item contract.

    :param client: TON client for blockchain interactions
    :param address: Telegram item contract address
    :return: Cell containing token name
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_telemint_token_name",
    )
    return t.cast(Cell, r[0])


class GetTelemintTokenNameGetMethod(ContractProtocol):
    """Mixin providing get_telemint_token_name() get method for Telegram items."""

    async def get_telemint_token_name(self) -> Cell:
        """
        Get token name from this Telegram item.

        Returns the username or gift name associated with this NFT.

        :return: Cell containing token name
        """
        return await get_telemint_token_name_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_auction_state_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get current auction state from a Telegram item contract.

    :param client: TON client for blockchain interactions
    :param address: Telegram item contract address
    :return: List containing auction state data (last bid, min bid, end time)
    """
    return await client.run_get_method(
        address=address,
        method_name="get_telemint_auction_state",
    )


class GetTelemintAuctionStateGetMethod(ContractProtocol):
    """Mixin providing get_telemint_auction_state() get method for Telegram items."""

    async def get_telemint_auction_state(self) -> t.List[t.Any]:
        """
        Get current auction state from this Telegram item.

        Returns auction state including last bid, minimum bid, and end time.

        :return: List containing auction state data
        """
        return await get_telemint_auction_state_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_auction_config_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get auction configuration from a Telegram item contract.

    :param client: TON client for blockchain interactions
    :param address: Telegram item contract address
    :return: List containing auction config data (beneficiary, bid limits, timing)
    """
    return await client.run_get_method(
        address=address,
        method_name="get_telemint_auction_config",
    )


class GetTelemintAuctionConfigGetMethod(ContractProtocol):
    """Mixin providing get_telemint_auction_config() get method for Telegram items."""

    async def get_telemint_auction_config(self) -> t.List[t.Any]:
        """
        Get auction configuration from this Telegram item.

        Returns auction parameters including beneficiary address, bid limits,
        minimum bid step, extension time, and duration.

        :return: List containing auction configuration data
        """
        return await get_telemint_auction_config_get_method(
            client=self.client,
            address=self.address,
        )
