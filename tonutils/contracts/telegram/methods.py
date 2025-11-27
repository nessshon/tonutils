import typing as t

from pytoniq_core import Cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike


async def get_full_domain_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    r = await client.run_get_method(
        address=address,
        method_name="get_full_domain",
    )
    return t.cast(Cell, r[0])


class GetFullDomainGetMethod(ContractProtocol):
    async def get_full_domain(self) -> Cell:
        return await get_full_domain_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_token_name_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Cell:
    r = await client.run_get_method(
        address=address,
        method_name="get_telemint_token_name",
    )
    return t.cast(Cell, r[0])


class GetTelemintTokenNameGetMethod(ContractProtocol):
    async def get_telemint_token_name(self) -> Cell:
        return await get_telemint_token_name_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_auction_state_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_telemint_auction_state",
    )


class GetTelemintAuctionStateGetMethod(ContractProtocol):
    async def get_telemint_auction_state(self) -> t.List[t.Any]:
        return await get_telemint_auction_state_get_method(
            client=self.client,
            address=self.address,
        )


async def get_telemint_auction_config_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_telemint_auction_config",
    )


class GetTelemintAuctionConfigGetMethod(ContractProtocol):
    async def get_telemint_auction_config(self) -> t.List[t.Any]:
        return await get_telemint_auction_config_get_method(
            client=self.client,
            address=self.address,
        )
