This section explains how to install the `tonutils` library and select the appropriate client depending on your needs.

---

## Installation

To install the base `tonutils` package:

```bash
pip install tonutils
```

If you need to use [Native ADNL](#pytoniq) connections, install with optional dependencies:

```bash
pip install 'tonutils[pytoniq]'
```

---

## Available Clients

### RPC API

#### toncenter

**[toncenter.com](https://toncenter.com)** — fast and reliable HTTP API for The Open Network.  

!!! note
    API key is optional, but for better performance it is recommended to obtain one via  [@tonapibot](https://t.me/tonapibot).

```python
from tonutils.client import ToncenterV2Client
from tonutils.client import ToncenterV3Client

API_KEY = "your api key"  # Optional
IS_TESTNET = True

# Using Toncenter V3 client
client_v3 = ToncenterV3Client(api_key=API_KEY, is_testnet=IS_TESTNET)

# Using Toncenter V2 client (if needed)
# client_v2 = ToncenterV2Client(api_key=API_KEY, is_testnet=IS_TESTNET)
```

---

#### tonapi

**[tonapi.io](https://tonapi.io)** — REST API to the TON blockchain explorer.  

!!! note
    Requires an API key from [tonconsole.com](https://tonconsole.com).

```python
from tonutils.client import TonapiClient

API_KEY = "your api key"
IS_TESTNET = True
client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

---

#### quicknode

**[quicknode.com](https://quicknode.com)** — low-latency HTTP API access to TON via global infrastructure.  

!!! note
    Requires an API URL from [quicknode.com](https://quicknode.com).

    Quicknode does not support testnet!

```python
from tonutils.client import QuicknodeClient

HTTP_PROVIDER_URL = "https://blissful-withered-surf.ton-mainnet.quiknode.pro/d6e8...1964"
client = QuicknodeClient(HTTP_PROVIDER_URL)
```

---

#### tatum

**[tatum.io](https://tatum.io)** — RPCs and APIs powering Web3.  

!!! note
    Requires an API key from [tatum.io](https://tatum.io).

```python
from tonutils.client import TatumClient

API_KEY = "your api key"
IS_TESTNET = True
client = TatumClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

---

### Native ADNL

#### pytoniq

**[pytoniq](https://github.com/yungwine/pytoniq)** — library for direct interaction with Lite servers.  

!!! note
    For better performance, provide your own config, which can be obtained from the [liteserver bot](https://t.me/liteserver_bot).

```python
from tonutils.client import LiteserverClient

IS_TESTNET = True
client = LiteserverClient(is_testnet=IS_TESTNET)

# Using custom configuration
# config = {}  # Your LiteServer config here 
# client = LiteserverClient(config=config)
```
