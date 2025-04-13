# 📦 Tonutils

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
[![PyPI](https://img.shields.io/pypi/v/tonutils.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/tonutils)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.12-black?color=FFE873&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/tonutils)](LICENSE)

![Image](https://telegra.ph//file/068ea06087c9ce8c6bfed.jpg)

![Downloads](https://pepy.tech/badge/tonutils)
![Downloads](https://pepy.tech/badge/tonutils/month)
![Downloads](https://pepy.tech/badge/tonutils/week)

**Tonutils** is a high-level object-oriented library for Python designed to facilitate interactions with the TON
blockchain. It seamlessly integrates three prominent services for working with TON:

- [tonapi.io](https://tonapi.io) - REST api to TON blockchain explorer.
- [toncenter.com](https://toncenter.com) - Fast and reliable HTTP API for The Open Network.
- [pytoniq](https://github.com/yungwine/pytoniq) - Library for direct interaction with Lite servers.
- [quicknode.com](https://www.quicknode.com/) - Low-latency HTTP API access to TON via global infrastructure.

By combining these services, Tonutils provides a powerful and flexible toolset for developers, making it easier to work
with the TON ecosystem.

## Installation

```bash
pip install tonutils
```

To use the `LiteserverClient`, which requires the [pytoniq](https://github.com/yungwine/pytoniq) library, install it
with the
optional dependencies:

```bash
pip install 'tonutils[pytoniq]'
```

## Donations

Your donation supports the future of this project. Every contribution helps stimulate innovation and sustain
development!

**TON** - `UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0`

**USDT** (TRC-20) - `TGKmm9H3FApFw8xcgRcZDHSku68vozAjo9`

## Usage

### Providers

<details>
<summary><b>• TonapiClient</b> To use you need to obtain an API key on the <a href="https://tonconsole.com" target="_blank">tonconsole.com</a>.</summary>

Client Initialization

```python
from tonutils.client import TonapiClient

API_KEY = "your api key"
IS_TESTNET = True
client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

</details>

<details>
<summary><b>• ToncenterClient</b> To use you need to obtain an API key from the <a href="https://t.me/tonapibot" target="_blank">bot</a>.</summary>

Client Initialization

```python
from tonutils.client import ToncenterClient

API_KEY = "your api key"  # optional 
IS_TESTNET = True
client = ToncenterClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

</details>

<details>
<summary><b>• LiteserverClient</b> For better performance, pass your own config, available from the <a href="https://t.me/liteserver_bot" target="_blank">bot</a>.</summary>

Client Initialization:

```python
from tonutils.client import LiteserverClient

config = {}  # your own config
IS_TESTNET = True
client = LiteserverClient(config=config, is_testnet=IS_TESTNET)
```

</details>

<details>
<summary><b>• QuicknodeClient</b> To use, obtain an API URL from <a href="https://quicknode.com" target="_blank">quicknode.com</a>.</summary>

**Note**: QuickNode does not support testnet.

Client Initialization:

```python
from tonutils.client import QuicknodeClient

HTTP_PROVIDER_URL = "https://blissful-withered-surf.ton-mainnet.quiknode.pro/d6e8...1964"
client = QuicknodeClient(HTTP_PROVIDER_URL)
```

</details>

### Guide

#### Getting Testnet Assets

- **TON**:  
  Obtain free testnet TON by interacting with the official bot:  
  [Open Bot](https://t.me/testgiver_ton_bot)

- **NOT Jettons** (9 decimals):  
  Claim testnet NOT by scanning the QR code at the following link:  
  [Scan to Claim Testnet NOT](https://qrcode.ness.su/create?data=ton%3A%2F%2Ftransfer%2FkQBMfIaxfLQMP4h1Pg2V_AuyToC3jdB8MmA6u3bx8i1__NOT%3Famount%3D100000000%26bin%3Dte6ccgEBAgEAKgABIWQrfQcAAAAAAAAAABAX14QCAQAnF41FGQAAAAAAAAAAXo1KUQAAEBQ%3D&border=3&box_size=30&image_url=https%3A%2F%2Fcdn.joincommunity.xyz%2Fclicker%2Fnot_logo.png&image_round=50&image_padding=60)

- **USD₮ Jettons** (6 decimals):  
  Claim testnet USD₮ by scanning the QR code at the following link:  
  [Scan to Claim Testnet USD₮](https://qrcode.ness.su/create?data=ton%3A%2F%2Ftransfer%2FkQB0ZYUL5M3KfrW0tSnwdFO1nC-BQHC2gcZl-WaF2on_USDT%3Famount%3D100000000%26bin%3Dte6ccgEBAgEAKQABIWQrfQcAAAAAAAAAABAX14QCAQAlF41FGQAAAAAAAAAAQ7msoAAQFA%3D%3D&border=3&box_size=30&image_url=https%3A%2F%2Ftether.to%2Fimages%2FlogoCircle.png&image_round=50&image_padding=99)

#### Ton Connect Integration

- [Wallet Connection](https://github.com/nessshon/tonutils/tree/main/examples/tonconnect/wallet_connection/)
- [Sending Transaction](https://github.com/nessshon/tonutils/tree/main/examples/tonconnect/sending_transaction/)
- [Telegram Bot Integration](https://github.com/nessshon/tonutils/tree/main/examples/tonconnect/telegram_bot/)

#### Wallet Operations

- [Create Wallet](https://github.com/nessshon/tonutils/tree/main/examples/wallet/create_wallet.py)
- [Deploy Wallet](https://github.com/nessshon/tonutils/tree/main/examples/wallet/deploy_wallet.py)
- [Encrypt Comment](https://github.com/nessshon/tonutils/tree/main/examples/wallet/encrypt_comment.py)
- [Get Wallet Balance](https://github.com/nessshon/tonutils/tree/main/examples/wallet/get_balance.py)
- [Gasless Transaction (Wallet v5 only)](https://github.com/nessshon/tonutils/tree/main/examples/wallet/gasless_transaction.py)

- ##### Standard Wallet

    - [Transfer TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/transfer_ton.py)
    - [Transfer NFT](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/transfer_nft.py)
    - [Transfer Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/transfer_jetton.py)

- ##### Highload Wallet

    - [Transfer TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/highload/transfer_ton.py)
    - [Transfer NFT](https://github.com/nessshon/tonutils/tree/main/examples/wallet/highload/transfer_nft.py)
    - [Transfer Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/highload/transfer_jetton.py)

- ##### Preprocessed Wallet

    - [Transfer TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/preprocessed/transfer_ton.py)
    - [Transfer NFT](https://github.com/nessshon/tonutils/tree/main/examples/wallet/preprocessed/transfer_nft.py)
    - [Transfer Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/preprocessed/transfer_jetton.py)

- ##### DEX DeDust.io

    - [Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/dedust/swap_ton_to_jetton.py)
    - [Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/dedust/swap_jetton_to_ton.py)
    - [Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/dedust/swap_jetton_to_jetton.py)
    - [Batch Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/dedust/batch_swap_ton_to_jetton.py)
    - [Batch Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/dedust/batch_swap_jetton_to_ton.py)
    - [Batch Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/dedust/batch_swap_jetton_to_jetton.py)

- ##### DEX STON.fi

    - [Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/stonfi/swap_ton_to_jetton.py)
    - [Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/stonfi/swap_jetton_to_ton.py)
    - [Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/stonfi/swap_jetton_to_jetton.py)
    - [Batch Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/stonfi/batch_swap_ton_to_jetton.py)
    - [Batch Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/stonfi/batch_swap_jetton_to_ton.py)
    - [Batch Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/wallet/common/dex/stonfi/batch_swap_jetton_to_jetton.py)

#### Jetton Operations

- [Transfer Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/transfer_jetton.py)
- [Get Jetton Wallet Balance](https://github.com/nessshon/tonutils/tree/main/examples/jetton/get_balance.py)

- ##### Mintless Jetton (e.g. Hamster)

    - [Claim Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/mintless/claim_jetton.py)
    - [Transfer Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/mintless/transfer_jetton.py)

- ##### Standard Jetton

    - [Deploy Jetton Master Offchain](https://github.com/nessshon/tonutils/tree/main/examples/jetton/standard/deploy_master.py)
    - [Deploy Jetton Master Onchain](https://github.com/nessshon/tonutils/tree/main/examples/jetton/standard/deploy_master_onchain.py)
    - [Mint Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/standard/mint_jetton.py)
    - [Burn Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/standard/burn_jetton.py)
    - [Change Admin](https://github.com/nessshon/tonutils/tree/main/examples/jetton/standard/change_admin.py)
    - [Change Content](https://github.com/nessshon/tonutils/tree/main/examples/jetton/standard/change_content.py)

- ##### Stablecoin Jetton (by Notcoin)

    - [Deploy Jetton Master](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/deploy_master.py)
    - [Upgrade Contract](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/upgrade_contract.py)
    - [Mint Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/mint_jetton.py)
    - [Burn Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/burn_jetton.py)
    - [Change Admin](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/change_admin.py)
    - [Drop Admin](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/drop_admin.py)
    - [Change Content](https://github.com/nessshon/tonutils/tree/main/examples/jetton/stablecoin/change_content.py)


- ##### DEX DeDust.io

    - [Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/dedust/swap_ton_to_jetton.py)
    - [Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/dedust/swap_jetton_to_ton.py)
    - [Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/dedust/swap_jetton_to_jetton.py)

- ##### DEX STON.fi (v1)
    - [Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/stonfi/v1/swap_ton_to_jetton.py)
    - [Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/stonfi/v1/swap_jetton_to_ton.py)
    - [Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/stonfi/v1/swap_jetton_to_jetton.py)

- ##### DEX STON.fi (v2)
    - [Swap TON to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/stonfi/v2/swap_ton_to_jetton.py)
    - [Swap Jetton to TON](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/stonfi/v2/swap_jetton_to_ton.py)
    - [Swap Jetton to Jetton](https://github.com/nessshon/tonutils/tree/main/examples/jetton/dex/stonfi/v2/swap_jetton_to_jetton.py)

#### NFT Operations

- [Deploy Onchain Collection](https://github.com/nessshon/tonutils/tree/main/examples/nft/deploy_onchain_collection.py)
- [Mint Onchain NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/mint_onchain_nft.py)
- [Transfer NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/transfer_nft.py)
- [Return Collection Balance](https://github.com/nessshon/tonutils/tree/main/examples/nft/return_collection_balance.py)

- ##### Editable NFTs

    - [Deploy Collection](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/deploy_collection.py)
    - [Mint NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/mint_nft.py)
    - [Batch Mint](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/batch_mint.py)
    - [Edit NFT Content](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/edit_nft_content.py)
    - [Change NFT Editorship](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/change_nft_editorship.py)
    - [Edit Collection Content](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/edit_collection_content.py)
    - [Change Collection Owner](https://github.com/nessshon/tonutils/tree/main/examples/nft/editbale/change_collection_owner.py)

- ##### Soulbound NFTs

    - [Deploy Collection](https://github.com/nessshon/tonutils/tree/main/examples/nft/soulbound/deploy_collection.py)
    - [Mint NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/soulbound/mint_nft.py)
    - [Batch Mint](https://github.com/nessshon/tonutils/tree/main/examples/nft/soulbound/batch_mint.py)
    - [Revoke NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/soulbound/revoke_nft.py)
    - [Destroy NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/soulbound/destroy_nft.py)

- ##### Standard NFTs

    - [Deploy Collection](https://github.com/nessshon/tonutils/tree/main/examples/nft/standard/deploy_collection.py)
    - [Mint NFT](https://github.com/nessshon/tonutils/tree/main/examples/nft/standard/mint_nft.py)
    - [Batch Mint](https://github.com/nessshon/tonutils/tree/main/examples/nft/standard/batch_mint.py)

- ##### Marketplace Getgems.io

    - [Put NFT On Sale](https://github.com/nessshon/tonutils/tree/main/examples/nft/marketplace/getgems/put_on_sale.py)
    - [Cancel NFT Sale](https://github.com/nessshon/tonutils/tree/main/examples/nft/marketplace/getgems/cancel_sale.py)
    - [Change NFT Price](https://github.com/nessshon/tonutils/tree/main/examples/nft/marketplace/getgems/change_price.py)

#### DNS Operations

- [Set Site Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/set_site.py)
- [Set Wallet Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/set_wallet.py)
- [Set Storage Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/set_storage.py)
- [Set Next Resolver Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/set_next_resolver.py)

- ##### DNS Subdomain Collection

    - [Deploy Collection](https://github.com/nessshon/tonutils/tree/main/examples/dns/collection/deploy_collection.py)
    - [Mint Subdomain](https://github.com/nessshon/tonutils/tree/main/examples/dns/collection/mint_subdomain.py)

- ##### Simple Subdomain Manager

    - [Deploy Manager](https://github.com/nessshon/tonutils/tree/main/examples/dns/simple_subdomain/deploy_manager.py)
    - [Set Site Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/simple_subdomain/set_site.py)
    - [Set Wallet Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/simple_subdomain/set_wallet.py)
    - [Set Storage Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/simple_subdomain/set_storage.py)
    - [Set Next Resolver Record](https://github.com/nessshon/tonutils/tree/main/examples/dns/simple_subdomain/set_next_resolver.py)

#### Vanity Operations

- [Deploy Contract](https://github.com/nessshon/tonutils/tree/main/examples/vanity/deploy_contract.py)

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## Support

Supported by [TON Society](https://github.com/ton-society/grants-and-bounties), Grants and Bounties program.\
With special thanks to [Igroman787](https://github.com/Igroman787) for the support.

## License

This repository is distributed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.
