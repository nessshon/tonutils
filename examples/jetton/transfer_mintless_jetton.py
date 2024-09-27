from typing import Any, Dict, Union

import aiohttp
from pytoniq_core import Address, Cell, Slice, StateInit, begin_cell

from tonutils.client import TonapiClient
from tonutils.jetton import JettonWallet
from tonutils.utils import to_amount
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the Jetton Mintless Master contract
JETTON_MASTER_ADDRESS = "EQAJ8uWd7EBqsmpSWaRdf_I-8R8-XHwh3gsNKhy-UrdrPcUo"  # noqa; Hamster

# The address of the recipient
DESTINATION_ADDRESS = "UQ..."

# Comment to include in the transfer payload
COMMENT = "Hello from tonutils!"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_payload = await get_jetton_payload(client, wallet.address.to_str())
    if jetton_payload is None:
        print("Error: Jetton payload not found. Are you sure there are jettons in this wallet?")
        return

    jetton_balance = int(jetton_payload["balance"])
    custom_payload_api_uri = jetton_payload["jetton"]["custom_payload_api_uri"]

    jetton_custom_payload = await get_jetton_custom_payload(custom_payload_api_uri, wallet.address.to_str())
    jetton_wallet_address = Address(jetton_custom_payload["jetton_wallet"])

    forward_payload = (
        begin_cell()
        .store_uint(0, 32)
        .store_snake_string(COMMENT)
        .end_cell()
    )

    custom_payload = Cell.one_from_boc(jetton_custom_payload["custom_payload"])
    state_init = StateInit.deserialize(Slice.one_from_boc(jetton_custom_payload["state_init"]))

    body = JettonWallet.build_transfer_body(
        recipient_address=Address(DESTINATION_ADDRESS),
        response_address=wallet.address,
        jetton_amount=jetton_balance,
        custom_payload=custom_payload,
        forward_payload=forward_payload,
        forward_amount=1,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_wallet_address,
        amount=0.1,
        body=body,
        state_init=state_init,
        bounce=True,
    )

    print(f"Successfully transferred {to_amount(jetton_balance)} jettons!")
    print(f"Transaction hash: {tx_hash}")


async def get_jetton_payload(client: TonapiClient, wallet_address: str) -> Union[Dict[str, Any], None]:
    method = f"/v2/accounts/{wallet_address}/jettons"
    params = {"supported_extensions": "custom_payload"}

    try:
        result = await client._request("GET", path=method, params=params)  # noqa
        return next(
            (balance for balance in result.get("balances", [])
             if Address(balance["jetton"]["address"]) == Address(JETTON_MASTER_ADDRESS)),
            None
        )
    except Exception as e:
        print(f"Error fetching jetton payload: {e}")
        return None


async def get_jetton_custom_payload(custom_payload_api_uri: str, wallet_address: str) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        url = f"{custom_payload_api_uri}/wallet/{wallet_address}"
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
