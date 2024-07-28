# 📦 Tonutils

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
[![PyPI](https://img.shields.io/pypi/v/tonutils.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/tonutils)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.11-black?color=FFE873&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/tonutils)](https://github.com/nessshon/tonutils/blob/main/LICENSE)

**Tonutils** is a high-level OOP library for Python designed for interacting with the TON. It is built on
top of three of the most popular libraries for working with TON in
Python: [pytoniq](https://github.com/yungwine/pytoniq), [pytonapi](https://github.com/tonkeeper/pytonapi),
and [pytoncenter](https://github.com/Ton-Dynasty/pytoncenter). By integrating these libraries, tonutils offers a
convenient and flexible tool for developers.

![Downloads](https://pepy.tech/badge/tonutils)
![Downloads](https://pepy.tech/badge/tonutils/month)
![Downloads](https://pepy.tech/badge/tonutils/week)
## Installation

```bash
pip install tonutils
```

## Usage

### Providers

- #### **LiteClient**
  Uses `LiteBalancer` from the [pytoniq](https://github.com/yungwine/pytoniq) library and interacts with the blockchain
  via lite servers.\
  For better performance, you can pass your own config from a private lite server, which can be acquired from the <a href="https://t.me/liteserver_bot" target="_blank">bot</a>.

  <details>
  <summary>Client Initialization</summary>

  ```python
  from tonutils.client import LiteClient

  config = None
  IS_TESTNET = True
  client = LiteClient(config=config, is_testnet=IS_TESTNET)
  ```

  </details>

- #### **TonapiClient**
  Uses `AsyncTonapi` from the [pytonapi](https://github.com/tonkeeper/pytonapi) library and interacts with the
  blockchain via the tonapi.io API.\
  To use you need to obtain an API key on the <a href="https://tonconsole.com" target="_blank">tonconsole.com</a>.

  <details>
  <summary>Client Initialization</summary>

  ```python
  from tonutils.client import TonapiClient

  API_KEY = ""
  IS_TESTNET = True
  client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
  ```

  </details>

- #### **ToncenterClient**
  Uses `AsyncTonCenterClientV3` from the [pytoncenter](https://github.com/Ton-Dynasty/pytoncenter) library and interacts
  with the blockchain via the toncenter.com API.\
  To use you need to obtain an API key from the <a href="https://t.me/tonapibot" target="_blank">bot</a>.

  <details>
  <summary>Client Initialization</summary>

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

## Contribution

We welcome your contributions! If you have ideas for improvement or have identified a bug, please create an issue or
submit a pull request.

## Donations

**TON** - `EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess`

**USDT** (TRC-20) - `TJjADKFT2i7jqNJAxkgeRm5o9uarcoLUeR`

## License

This repository is distributed under the [MIT License](https://github.com/nessshon/tonutils/blob/main/LICENSE).
Feel free to use, modify, and distribute the code in accordance with the terms of the license.
