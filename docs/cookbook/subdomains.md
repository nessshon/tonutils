## Introduction

This guide walks you through creating and managing **subdomains on the TON blockchain** using open-source tools. It covers deploying subdomain management contracts, issuing subdomains, and managing DNS records with practical examples.

## Implementation

There are two open-source implementations available for managing subdomains on TON, depending on the level of complexity and control you need:

### Subdomain Collection

[GitHub ↗](https://github.com/nessshon/subdomains-toolbox/tree/main/collection-contracts/admin-mint)

This is a more advanced solution where each subdomain is represented as an NFT. The owner of the collection is responsible for issuing subdomains, while each NFT owner has full control over their subdomain.

**Key Features:**

- Subdomains can be transferred or sold
- Decentralized record management — each subdomain has its own smart contract
- Requires additional infrastructure (e.g., metadata API)

### Subdomain Manager

[GitHub ↗](https://github.com/Gusarich/simple-subdomain)

This is a basic implementation where a single smart contract acts as the centralized subdomain manager. The administrator is responsible for issuing subdomains and configuring their DNS records.

**Key Features:**

- Suitable for simple use cases
- Quick and easy setup
- Centralized control through one smart contract

## Environment Setup

This guide uses **Python** along with the open-source **tonutils** library, which supports both subdomain management implementations.

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

### Additional Requirements for Subdomain Collection

If you’re using the Subdomain Collection approach, you’ll also need:

- A server to host the **metadata API**
- A **domain name** pointing to that server for metadata access
- **Docker** and **Docker Compose** for easy deployment of the API

## Subdomain Collection

### Metadata Setup

Before deploying the subdomain collection, you need to launch the metadata API. This service is responsible for generating dynamic images and attributes for your subdomain NFTs, making them visually identifiable.

1. Clone the repository:

   ```bash
   git clone https://github.com/nessshon/subdomains-toolbox
   cd metadata-api
   ```

2. Start the API using Docker:  
   The API will be running on port `8001`. You will need to configure SSL and set up a reverse proxy to expose it securely.

   ```bash
   docker-compose up -d
   ```

3. Test the API:  
   Visit `https://your-domain.com/api/ton/example.png` in your browser. If set up correctly, you’ll see a generated image for the subdomain `example`.

### Deploy the Collection

Once the API is running, you can deploy the NFT collection smart contract for your subdomains.

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns import Domain
from tonutils.dns.subdomain_collection import SubdomainCollection
from tonutils.dns.subdomain_collection.content import SubdomainCollectionContent
from tonutils.dns.subdomain_collection.data import FullDomain
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import TransferMessage

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# NFT domain name and address from TON DNS Domains
# Obtainable from https://dns.ton.org/ or https://dns.ton.org/?testnet=true
DOMAIN_NAME = "ghost"  # ghost → ghost.ton
DOMAIN_ADDRESS = "EQ..."

# Royalty parameters: base and factor for calculating the royalty
ROYALTY_BASE = 1000
ROYALTY_FACTOR = 55  # 5.5% royalty

# Base URL of the API for generating metadata for NFTs
# API source code: https://github.com/nessshon/subdomains-toolbox
API_BASE_URL = "https://your-domain.com/api/ton/"

# Metadata for the NFT collection
COLLECTION_METADATA = {
    "name": f"{DOMAIN_NAME.title()} DNS Domains",
    "image": f"{API_BASE_URL}{DOMAIN_NAME}.png",
    "description": f"*.{DOMAIN_NAME}.ton domains",
    "prefix_uri": API_BASE_URL,
}
"""
Example of the metadata for the NFT collection (JSON format):
{
    "name": "Ghost DNS Domains",
    "image": "https://your-domain.com/api/ton/ghost.png",
    "description": "*.ghost.ton domains",
    "prefix_uri": "https://your-domain.com/api/ton/"
}
"""


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    collection = SubdomainCollection(
        owner_address=wallet.address,
        content=SubdomainCollectionContent(**COLLECTION_METADATA),
        royalty_params=RoyaltyParams(
            base=ROYALTY_BASE,
            factor=ROYALTY_FACTOR,
            address=wallet.address,
        ),
        full_domain=FullDomain(DOMAIN_NAME, "ton"),
    )

    tx_hash = await wallet.batch_transfer(
        [
            # Deploy collection
            TransferMessage(
                destination=collection.address,
                amount=0.05,
                body=collection.build_deploy_body(),
                state_init=collection.state_init,
            ),
            # Bind Subdomain Collection to the main domain
            TransferMessage(
                destination=DOMAIN_ADDRESS,
                amount=0.05,
                body=Domain.build_set_next_resolver_record_body(collection.address),
            ),
        ]
    )

    print(f"Successfully deployed Subdomain Collection at address: {collection.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Minting Subdomains

To mint a new subdomain as an NFT:

1. Open your TON wallet (e.g., Tonkeeper).
2. Send **0.1 TON** to the Subdomain Collection contract address (printed during deployment).
3. In the transaction comment field, enter the desired subdomain name (e.g., `alice` for `alice.ghost.ton`).
4. Ensure the subdomain name is valid (alphanumeric, no special characters) and not already minted.
5. After the transaction is confirmed, the subdomain NFT will be sent to your wallet.

### Managing Records

#### Setting Records

The record-setting mechanism for NFT subdomains is similar to the one used in the **TON DNS Domains** collection. You can assign one of the following record types to a subdomain — examples for each are provided below.

<details>
  <summary><strong>Set Wallet Record</strong></summary>

```python
import asyncio
from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."

# Address of the wallet to be set (e.g., UQ...)
WALLET_ADDRESS = "UQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_wallet_record_body(Address(WALLET_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
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
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."

# ADNL address (e.g., "a1b2c3...")
ADNL_ADDRESS = "a1b2c3..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_site_record_body(ADNL_ADDRESS)

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
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
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."

# Hex-encoded BAG ID (e.g., "1234567890abcdef...")
BAG_ID = "1234567890abcdef..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_storage_record_body(BAG_ID)

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
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
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."

# Address of the next resolver contract (e.g., EQ...)
CONTRACT_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_next_resolver_record_body(Address(CONTRACT_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

#### Deleting Records

Similarly, you can delete existing records. Below are examples for each type.

<details>
  <summary><strong>Delete Wallet Record</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_delete_wallet_record_body()

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
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
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_delete_site_record_body()

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
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
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_delete_storage_record_body()

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
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
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# Set to True for test network
IS_TESTNET = True

# Mnemonic phrase for the wallet (list of 24 words, e.g., ["word1", "word2", ...])
MNEMONIC: list[str] = []

# Address of the NFT subdomain (e.g., EQ...)
NFT_DOMAIN_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_delete_next_resolver_record_body()

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.005,
        body=body,
    )
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

## Subdomain Manager

### Deploy the Manager

Below is an example of how to deploy the Subdomain Manager using the tonutils Python library. This script initializes the smart contract, links it to the main domain, and sends the necessary transactions from your wallet.

```python
import asyncio
from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns import Domain
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
                body=Domain.build_set_next_resolver_record_body(subdomain_manager.address),
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

Conclusion
----------

TON blockchain offers flexible options for subdomain management, whether you prefer a centralized approach with the Subdomain Manager or a decentralized, NFT-based solution with the Subdomain Collection. Both solutions are easy to implement and provide powerful tools to manage your subdomains and DNS records efficiently. This guide provides all the necessary steps to get started and take control of your subdomains on TON.

See also
--------

* [TON Subdomains Toolbox](https://github.com/nessshon/subdomains-toolbox)
* [Subdomain Manager Contract](https://github.com/Gusarich/simple-subdomain)
* [Subdomain Collection Contract](https://github.com/nessshon/subdomains-toolbox/tree/main/collection-contracts/admin-mint)
