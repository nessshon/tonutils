# 📦 Tonutils

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
[![PyPI](https://img.shields.io/pypi/v/tonutils.svg?color=FFE873&labelColor=3776AB)](https://pypi.python.org/pypi/tonutils)
![Python Versions](https://img.shields.io/badge/Python-3.10%20--%203.12-black?color=FFE873&labelColor=3776AB)
[![License](https://img.shields.io/github/license/nessshon/tonutils)](LICENSE)

![Image](https://telegra.ph//file/068ea06087c9ce8c6bfed.jpg)

![Downloads](https://pepy.tech/badge/tonutils)
![Downloads](https://pepy.tech/badge/tonutils/month)
![Downloads](https://pepy.tech/badge/tonutils/week)

**Tonutils** is a high-level, object-oriented Python library designed to simplify interactions with the TON blockchain.
It seamlessly integrates several prominent services for working with TON:

* **RPC API**
    * [tonapi.io](https://tonapi.io) – REST API to the TON blockchain explorer.
    * [toncenter.com](https://toncenter.com) – fast and reliable HTTP API for The Open Network.
    * [quicknode.com](https://www.quicknode.com/) – low-latency HTTP API access to TON via global infrastructure.
    * [tatum.io](https://tatum.io) – RPCs and APIs powering Web3. Fast, reliable, affordable.

* **Native ADNL**
    * [pytoniq](https://github.com/yungwine/pytoniq) – library for direct interaction with Lite servers.

By combining these services, Tonutils provides a powerful and flexible toolset for developers, making it easier to build
on top of the TON ecosystem.

## Installation

```bash
pip install "tonutils<2.0"
```

To use `pytoniq` with Native ADNL connection, install it with the optional dependencies, including
the [pytoniq](https://github.com/yungwine/pytoniq) library:

```bash
pip install "tonutils[pytoniq]<2.0"
```

## Documentation

Find all guides and references here:  
[nessshon.github.io/tonutils](https://nessshon.github.io/tonutils/)

## Donations

If this project has been useful to you, consider supporting its development!

**TON**: `UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness`

## Support

Supported by [TON Society](https://github.com/ton-society/grants-and-bounties), Grants and Bounties program.\
With special thanks to [Igroman787](https://github.com/Igroman787) for the support.

## License

This repository is distributed under the [MIT License](LICENSE).
