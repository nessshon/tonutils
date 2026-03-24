# 📦 Tonutils

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.14-black?color=FFE873&labelColor=3776AB)
[![PyPI](https://img.shields.io/pypi/v/tonutils.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/tonutils)
[![License](https://img.shields.io/github/license/nessshon/tonutils)](https://github.com/nessshon/tonutils/blob/main/LICENSE)
[![Donate](https://img.shields.io/badge/Donate-TON-blue)](https://tonviewer.com/UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness)

![Image](https://raw.githubusercontent.com/nessshon/tonutils/main/assets/banner.png)

![Downloads](https://pepy.tech/badge/tonutils)
![Downloads](https://pepy.tech/badge/tonutils/month)
![Downloads](https://pepy.tech/badge/tonutils/week)

### Python SDK for [TON Blockchain](https://ton.org)

Interact with the TON blockchain via lite servers (ADNL) and HTTP API providers.
Wallets, transfers, smart contracts, and on-chain tools — all in one async-first package.

**Features**

- **Providers** — Lite Servers (ADNL), HTTP (Toncenter, TONAPI, etc.)
- **Wallets** — V1–V5, Highload, Preprocessed; create, import, deploy
- **Transfers** — TON, Jetton, NFT, batch, gasless, encrypted messages
- **Contracts** — Jettons, NFTs, DNS, Telegram; deploy, mint, manage
- **Tools** — lite-server monitor, block scanner, CLI

> Support this project — TON: `donate.ness.ton`  
> `UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness`

## Installation

```bash
pip install tonutils
```

## Examples

- [Client initialization](https://github.com/nessshon/tonutils/blob/main/examples/client/)
- [Create Wallet](https://github.com/nessshon/tonutils/blob/main/examples/wallet/create_wallet.py)
- [Import Wallet](https://github.com/nessshon/tonutils/blob/main/examples/wallet/import_wallet.py)
- [Deploy Wallet](https://github.com/nessshon/tonutils/blob/main/examples/wallet/deploy_wallet.py)
- [Wallet Info](https://github.com/nessshon/tonutils/blob/main/examples/wallet/wallet_info.py)
- [Block Scanner](https://github.com/nessshon/tonutils/blob/main/examples/block_scanner.py)
- [Vanity Contract](https://github.com/nessshon/tonutils/blob/main/examples/vanity/deploy_contract.py)

**Transfers**

- [TON Transfer](https://github.com/nessshon/tonutils/blob/main/examples/wallet/ton_transfer.py)
- [Jetton Transfer](https://github.com/nessshon/tonutils/blob/main/examples/wallet/jetton_transfer.py)
- [NFT Transfer](https://github.com/nessshon/tonutils/blob/main/examples/wallet/nft_transfer.py)
- [Batch Transfer](https://github.com/nessshon/tonutils/blob/main/examples/wallet/batch_transfer.py)
- [Gasless Transfer](https://github.com/nessshon/tonutils/blob/main/examples/wallet/gasless_transfer.py)
- [Encrypt Message](https://github.com/nessshon/tonutils/blob/main/examples/wallet/encrypt_message.py)
- [Decrypt Message](https://github.com/nessshon/tonutils/blob/main/examples/wallet/decrypt_message.py)

**Jetton**

- [Stablecoin](https://github.com/nessshon/tonutils/blob/main/examples/jetton/stablecoin/)
- [Standard](https://github.com/nessshon/tonutils/blob/main/examples/jetton/standard/)

**NFT**

- [Editable](https://github.com/nessshon/tonutils/blob/main/examples/nft/editable/)
- [Soulbound](https://github.com/nessshon/tonutils/blob/main/examples/nft/soulbound/)
- [Standard](https://github.com/nessshon/tonutils/blob/main/examples/nft/standard/)

**DNS**

- [Resolve](https://github.com/nessshon/tonutils/blob/main/examples/dns/dns_resolve.py)
- [Get Records](https://github.com/nessshon/tonutils/blob/main/examples/dns/get_records.py)
- [Set Records](https://github.com/nessshon/tonutils/blob/main/examples/dns/set_records.py)

## CLI

Show version:

```bash
tonutils -v
```

Monitor lite-server availability:

```bash
tonutils status [-n mainnet|testnet] [-c PATH_OR_URL] [-r RPS]
```

## License

This repository is distributed under the [MIT License](https://github.com/nessshon/tonutils/blob/main/LICENSE).
