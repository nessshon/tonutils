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

By combining these services, Tonutils provides a powerful and flexible toolset for developers, making it easier to work
with the TON ecosystem.

## Installation

```bash
pip install tonutils
```

To use the `LiteClient`, which requires the [pytoniq](https://github.com/yungwine/pytoniq) library, install it with the
optional dependencies:

```bash
pip install 'tonutils[pytoniq]'
```

## Usage

### Providers

<details>
<summary><b>• LiteClient</b> For better performance, pass your own config, available from the <a href="https://t.me/liteserver_bot" target="_blank">bot</a>.</summary>

Client Initialization:

```python
from tonutils.client import LiteClient

config = None
IS_TESTNET = True
client = LiteClient(config=config, is_testnet=IS_TESTNET)
```

</details>

<details>
<summary><b>• TonapiClient</b> To use you need to obtain an API key on the <a href="https://tonconsole.com" target="_blank">tonconsole.com</a>.</summary>

Client Initialization

```python
from tonutils.client import TonapiClient

API_KEY = ""
IS_TESTNET = True
client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

</details>

<details>
<summary><b>• ToncenterClient</b> To use you need to obtain an API key from the <a href="https://t.me/tonapibot" target="_blank">bot</a>.</summary>

Client Initialization

```python
from tonutils.client import ToncenterClient

API_KEY = ""
IS_TESTNET = True
client = ToncenterClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

</details>

### Guide

#### Wallet Operations

- [Create Wallet](examples/wallet/create_wallet.py)
- [Deploy Wallet](examples/wallet/deploy_wallet.py)
- [Get Wallet Balance](examples/wallet/get_balance.py)
- [Encrypt Comment](examples/wallet/encrypt_comment.py)

- ##### Standard Wallet

  - [Transfer TON](examples/wallet/common/transfer_ton.py)
  - [Transfer NFT](examples/wallet/common/transfer_nft.py)
  - [Transfer Jetton](examples/wallet/common/transfer_jetton.py)
  - [Swap TON to Jetton](examples/wallet/common/dex/dedust/swap_ton_to_jetton.py)
  - [Swap Jetton to TON](examples/wallet/common/dex/dedust/swap_jetton_to_ton.py)
  - [Swap Jetton to Jetton](examples/wallet/common/dex/dedust/swap_jetton_to_jetton.py)
  - [Batch Transfer TON](examples/wallet/common/batch_transfer_ton.py)
  - [Batch Transfer NFT](examples/wallet/common/batch_transfer_nft.py)
  - [Batch Transfer Jetton](examples/wallet/common/batch_transfer_jetton.py)

- ##### Highload Wallet

  - [Transfer TON](examples/wallet/highload/transfer_ton.py)
  - [Transfer NFT](examples/wallet/highload/transfer_nft.py)
  - [Transfer Jetton](examples/wallet/highload/transfer_jetton.py)
  - [Swap TON to Jetton](examples/wallet/highload/dex/dedust/swap_ton_to_jetton.py)
  - [Swap Jetton to TON](examples/wallet/highload/dex/dedust/swap_jetton_to_ton.py)
  - [Swap Jetton to Jetton](examples/wallet/highload/dex/dedust/swap_jetton_to_jetton.py)

#### Jetton Operations

- [Deploy Jetton Master Offchain](examples/jetton/deploy_master.py)
- [Deploy Jetton Master Onchain](examples/jetton/deploy_master_onchain.py)
- [Mint Jetton](examples/jetton/mint_jetton.py)
- [Burn Jetton](examples/jetton/burn_jetton.py)
- [Change Admin](examples/jetton/change_admin.py)
- [Transfer Jetton](examples/jetton/transfer_jetton.py)
- [Get Jetton Wallet Balance](examples/jetton/get_balance.py)

- ##### DEX DeDust.io

  - [Swap TON to Jetton](examples/jetton/dex/dedust/swap_ton_to_jetton.py)
  - [Swap Jetton to TON](examples/jetton/dex/dedust/swap_jetton_to_ton.py)
  - [Swap Jetton to Jetton](examples/jetton/dex/dedust/swap_jetton_to_jetton.py)

#### NFT Operations

- [Deploy Onchain Collection](examples/nft/deploy_onchain_collection.py)
- [Mint Onchain NFT](examples/nft/mint_onchain_nft.py)
- [Transfer NFT](examples/nft/transfer_nft.py)
- [Return Collection Balance](examples/nft/return_collection_balance.py)

- ##### Editable NFTs

  - [Deploy Collection](examples/nft/editbale/deploy_collection.py)
  - [Mint NFT](examples/nft/editbale/mint_nft.py)
  - [Batch Mint](examples/nft/editbale/batch_mint.py)
  - [Edit NFT Content](examples/nft/editbale/edit_nft_content.py)
  - [Change NFT Editorship](examples/nft/editbale/change_nft_editorship.py)
  - [Edit Collection Content](examples/nft/editbale/edit_collection_content.py)
  - [Change Collection Owner](examples/nft/editbale/change_collection_owner.py)

- ##### Soulbound NFTs

  - [Deploy Collection](examples/nft/soulbound/deploy_collection.py)
  - [Mint NFT](examples/nft/soulbound/mint_nft.py)
  - [Batch Mint](examples/nft/soulbound/batch_mint.py)
  - [Revoke NFT](examples/nft/soulbound/revoke_nft.py)
  - [Destroy NFT](examples/nft/soulbound/destroy_nft.py)

- ##### Standard NFTs

  - [Deploy Collection](examples/nft/standard/deploy_collection.py)
  - [Mint NFT](examples/nft/standard/mint_nft.py)
  - [Batch Mint](examples/nft/standard/batch_mint.py)

- ##### Marketplace Getgems.io

  - [Put NFT On Sale](examples/nft/marketplace/getgems/put_on_sale.py)
  - [Cancel NFT Sale](examples/nft/marketplace/getgems/cancel_sale.py)
  - [Change NFT Price](examples/nft/marketplace/getgems/change_price.py)

#### DNS Operations

- [Set Site Record](examples/dns/set_site.py)
- [Set Wallet Record](examples/dns/set_wallet.py)
- [Set Storage Record](examples/dns/set_storage.py)
- [Set Next Resolver Record](examples/dns/set_next_resolver.py)

- ##### Simple Subdomain Manager

  - [Deploy Manager](examples/dns/simple_subdomain/deploy_manager.py)
  - [Set Site Record](examples/dns/simple_subdomain/set_site.py)
  - [Set Wallet Record](examples/dns/simple_subdomain/set_wallet.py)
  - [Set Storage Record](examples/dns/simple_subdomain/set_storage.py)
  - [Set Next Resolver Record](examples/dns/simple_subdomain/set_next_resolver.py)

#### Vanity Operations

- [Deploy Contract](examples/vanity/deploy_contract.py)

## Donations

Your donation supports the future of this project. Every contribution helps stimulate innovation and sustain
development!

**TON** - `EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess`

**USDT** (TRC-20) - `TGKmm9H3FApFw8xcgRcZDHSku68vozAjo9`

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## License

This repository is distributed under the [MIT License](LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.
