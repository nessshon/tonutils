from typing import Tuple, Union

from pytoniq_core import Address

from . import StonfiRouterV1, StonfiRouterV2
from .v1.pton.constants import PTONAddresses as PTONAddressesV1
from .v2.pton.constants import PTONAddresses as PTONAddressesV2


async def get_stonfi_router_details(
        offer_address: str,
        ask_address: str,
        amount: Union[int, float],
        decimals: int,
        is_testnet: bool,
) -> Tuple[int, Address, Address]:
    pton_v1 = PTONAddressesV1.TESTNET if is_testnet else PTONAddressesV1.MAINNET
    pton_v2 = PTONAddressesV2.TESTNET if is_testnet else PTONAddressesV2.MAINNET

    def resolve_pton_address(address: str, pton_address: str) -> str:
        return pton_address if address == "ton" else address

    try:
        version = 2
        pton = pton_v2
        offer = resolve_pton_address(offer_address, pton)
        ask = resolve_pton_address(ask_address, pton)
        router_address = await StonfiRouterV2.get_router_address(
            offer_address=offer,
            ask_address=ask,
            amount=amount,
            decimals=decimals,
        )

    except ValueError:
        version = 1
        pton = pton_v1
        offer = resolve_pton_address(offer_address, pton)
        ask = resolve_pton_address(ask_address, pton)
        router_address = await StonfiRouterV1.get_router_address(
            offer_address=offer,
            ask_address=ask,
            amount=amount,
            decimals=decimals,
        )

    return version, Address(router_address), Address(pton)
