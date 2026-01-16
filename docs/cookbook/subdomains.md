## Introduction

This guide walks you through creating and managing **subdomains on the TON blockchain** using open-source tools. It
covers deploying subdomain management contracts, issuing subdomains, and managing DNS records with practical examples.

## Implementation

### Subdomain Manager

[GitHub ↗](https://github.com/Gusarich/simple-subdomain)

This is a basic implementation where a single smart contract acts as the centralized subdomain manager. The
administrator is responsible for issuing subdomains and configuring their DNS records.

**Key Features:**

- Suitable for simple use cases
- Quick and easy setup
- Centralized control through one smart contract

## Environment Setup

This guide uses **Python** along with the open-source **tonutils** library.

### Prerequisites

* **Python 3.10+**
* A registered **.ton domain**:
    * Mainnet: [dns.ton.org](https://dns.ton.org)
    * Testnet: [dns.ton.org?testnet=true](https://dns.ton.org?testnet=true)

### Install Dependencies

Install the required Python library:

```bash
pip install tonutils
```

## Subdomain Manager

### Deploy the Manager

Below is an example of how to deploy the Subdomain Manager using the tonutils Python library. This script initializes
the smart contract, links it to the main domain, and sends the necessary transactions from your wallet.

```python
import asyncio
from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns import DNS
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import TransferMessage

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Administrator address for managing the Subdomain Manager (e.g., UQ...)
ADMIN_ADDRESS = "UQ..."

# NFT address of the main domain from TON DNS Domains collection (e.g., EQ...)
DOMAIN_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    subdomain_manager = SubdomainManager(Address(ADMIN_ADDRESS))

    tx_hash = await wallet.batch_transfer(
        [
            # Deploy Subdomain Manager
            TransferMessage(
                destination=subdomain_manager.address,
                amount=0.05,
                state_init=subdomain_manager.state_init,
            ),
            # Bind Subdomain Manager to the main domain as a next resolver
            TransferMessage(
                destination=DOMAIN_ADDRESS,
                amount=0.05,
                body=DNS.build_set_next_resolver_record_body(subdomain_manager.address),
            ),
        ]
    )

    print(f"Successfully deployed Subdomain Manager at address: {subdomain_manager.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Setting Records

You can set one of the following record types for a subdomain. Below are examples for each.

<details>
  <summary><strong>Set Wallet Record</strong></summary>

```python
import asyncio
from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# Address of the wallet to be set for the subdomain (e.g., UQ...)
WALLET_ADDRESS = "UQ..."

# Subdomain to be registered (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_set_wallet_record_body(SUBDOMAIN, Address(WALLET_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
  <summary><strong>Set Site Record</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# ADNL address for the subdomain (e.g., "a1b2c3...")
ADNL_ADDRESS = "a1b2c3..."

# Subdomain to be registered (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_set_site_record_body(SUBDOMAIN, ADNL_ADDRESS)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
  <summary><strong>Set TON Storage Record</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# ID of the storage bag (hex string, e.g., "1234567890abcdef...")
BAG_ID = "1234567890abcdef..."

# Subdomain to be registered (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_set_storage_record_body(SUBDOMAIN, BAG_ID)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
  <summary><strong>Set Next Resolver Record</strong></summary>

```python
import asyncio

from pytoniq_core import Address
from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# Address of the next resolver contract (e.g., EQ...)
CONTRACT_ADDRESS = "EQ..."

# Subdomain to be registered (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_set_next_resolver_record_body(SUBDOMAIN, Address(CONTRACT_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

### Deleting Records

Similarly, you can delete existing records. Below are examples for each type.

<details>
  <summary>Delete Wallet Record</summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# Subdomain to be deleted (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_delete_wallet_record_body(SUBDOMAIN)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
  <summary><strong>Delete Site Record</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# Subdomain to be deleted (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_delete_site_record_body(SUBDOMAIN, False)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
  <summary><strong>Delete TON Storage Record</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# Subdomain to be deleted (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_delete_storage_record_body(SUBDOMAIN, True)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
  <summary><strong>Delete Next Resolver Record</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the subdomain manager contract (e.g., EQ...)
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# Subdomain to be deleted (e.g., "example" for example.your-domain.ton)
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_delete_next_resolver_record_body(SUBDOMAIN)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

See also
--------

* [Subdomain Manager Contract](https://github.com/Gusarich/simple-subdomain)
