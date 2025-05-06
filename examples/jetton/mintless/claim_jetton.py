from typing import Any, Dict, Union

import aiohttp
from aiohttp import ClientResponseError
from pytoniq_core import Address, Cell, Slice, StateInit

from tonutils.client import TonapiClient
from tonutils.jetton import JettonWalletStandard
from tonutils.utils import to_amount
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_data = await get_jetton(client, wallet.address.to_str())
    if jetton_data is None:
        raise Exception("Jetton data not found. Are there jettons in this wallet?")

    jetton_balance = int(jetton_data["balance"])
    custom_payload_api_uri = jetton_data["jetton"]["custom_payload_api_uri"]
    jetton_custom_payload = await get_payload(custom_payload_api_uri, wallet.address.to_str())
    jetton_wallet_address = jetton_custom_payload["jetton_wallet"]

    if not await is_claimed(client, jetton_wallet_address):
        custom_payload = Cell.one_from_boc(jetton_custom_payload["custom_payload"])
        state_init = StateInit.deserialize(Slice.one_from_boc(jetton_custom_payload["state_init"]))
    else:
        print("Jetton already claimed!")
        return

    body = JettonWalletStandard.build_transfer_body(
        recipient_address=wallet.address,
        response_address=wallet.address,
        jetton_amount=jetton_balance,
        custom_payload=custom_payload,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_wallet_address,
        amount=0.1,
        body=body,
        state_init=state_init,
        bounce=True,
    )

    print(f"Successfully claimed {to_amount(jetton_balance)} jettons!")
    print(f"Transaction hash: {tx_hash}")


async def get_jetton(client: TonapiClient, addr: str) -> Union[Dict[str, Any], None]:
    method = f"/v2/accounts/{addr}/jettons"
    params = {"supported_extensions": "custom_payload"}
    try:
        result = await client._request("GET", path=method, params=params)  # noqa
        return next(
            (b for b in result.get("balances", [])
             if Address(b["jetton"]["address"]) == Address(JETTON_MASTER_ADDRESS)),
            None
        )
    except Exception as e:
        print(f"Error fetching jetton data: {e}")
        return None


async def get_payload(api_uri: str, wallet_address: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_uri}/wallet/{wallet_address}") as response:
            response.raise_for_status()
            return await response.json()


async def is_claimed(client: TonapiClient, jetton_addr: str) -> bool:
    try:
        result = await client.run_get_method(jetton_addr, "is_claimed")
        return bool(result[0])
    except ClientResponseError as e:
        if e.status == 404:
            return False
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
