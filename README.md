# 📦 Tonutils

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
[![PyPI](https://img.shields.io/pypi/v/tonutils.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/tonutils)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.11-black?color=FFE873&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/tonutils)](https://github.com/nessshon/tonutils/blob/main/LICENSE)

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

### Wallet Operation Guide

- [Create Wallet](https://github.com/nessshon/tonutils/blob/main/examples/wallet/create_wallet.py)
- [Deploy Wallet](https://github.com/nessshon/tonutils/blob/main/examples/wallet/deploy_wallet.py)
- [Encrypt Comment](https://github.com/nessshon/tonutils/blob/main/examples/wallet/encrypt_comment.py)

- ##### **Common Wallet**

    - [Transfer TON](https://github.com/nessshon/tonutils/blob/main/examples/wallet/common/transfer_ton.py)
    - [Transfer NFT](https://github.com/nessshon/tonutils/blob/main/examples/wallet/common/transfer_nft.py)
    - [Transfer Jetton](https://github.com/nessshon/tonutils/blob/main/examples/wallet/common/transfer_jetton.py)
    - [Batch Transfer TON](https://github.com/nessshon/tonutils/blob/main/examples/wallet/common/batch_transfer_ton.py)
    - [Batch Transfer NFT](https://github.com/nessshon/tonutils/blob/main/examples/wallet/common/batch_transfer_nft.py)
    - [Batch Transfer Jetton](https://github.com/nessshon/tonutils/blob/main/examples/wallet/common/batch_transfer_jetton.py)

- ##### **Highload Wallet**
    - [Transfer TON](https://github.com/nessshon/tonutils/blob/main/examples/wallet/highload/transfer_ton.py)
    - [Transfer NFT](https://github.com/nessshon/tonutils/blob/main/examples/wallet/highload/transfer_nft.py)
    - [Transfer Jetton](https://github.com/nessshon/tonutils/blob/main/examples/wallet/highload/transfer_jetton.py)

### NFT Operations Guide

- ##### **Standard NFTs**

    - [Deploy Collection](https://github.com/nessshon/tonutils/blob/main/examples/nft/standard/deploy_collection.py)
    - [Mint Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/standard/mint_item.py)
    - [Batch Mint](https://github.com/nessshon/tonutils/blob/main/examples/nft/standard/batch_mint.py)
    - [Transfer Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/transfer_item.py)

- ##### **Editable NFTs**

    - [Deploy Collection](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/deploy_collection.py)
    - [Mint Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/mint_item.py)
    - [Batch Mint](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/batch_mint.py)
    - [Transfer Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/transfer_item.py)
    - [Edit Item Content](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/edit_item_content.py)
    - [Change Item Editorship](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/change_item_editorship.py)
    - [Edit Collection Content](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/edit_collection_content.py)
    - [Change Collection Owner](https://github.com/nessshon/tonutils/blob/main/examples/nft/editbale/change_collection_owner.py)

- ##### **Soulbound NFTs**

    - [Deploy Collection](https://github.com/nessshon/tonutils/blob/main/examples/nft/soulbound/deploy_collection.py)
    - [Mint Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/soulbound/mint_item.py)
    - [Batch Mint](https://github.com/nessshon/tonutils/blob/main/examples/nft/soulbound/batch_mint.py)
    - [Revoke Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/soulbound/revoke_item.py)
    - [Destroy Item](https://github.com/nessshon/tonutils/blob/main/examples/nft/soulbound/destroy_item.py)

## Donations

**TON** - `EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess`

**USDT** (TRC-20) - `TXuPpjZvqhjM3X7BFnzR6bBarB6svmCpt8`

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## Support

Supported by [TON Society](https://github.com/ton-society/grants-and-bounties), Grants and Bounties program.

## License

This repository is distributed under the [MIT License](https://github.com/nessshon/tonutils/blob/main/LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.
