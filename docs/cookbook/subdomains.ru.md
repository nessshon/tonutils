## Введение

Это руководство проведёт вас через процесс создания и управления **поддоменами в блокчейне TON** с использованием
инструментов с открытым исходным кодом. Оно охватывает развертывание контрактов управления поддоменами, выпуск
поддоменов и управление DNS-записями с практическими примерами.

## Реализация

### Менеджер поддоменов

[GitHub ↗](https://github.com/Gusarich/simple-subdomain)

Это базовая реализация, где один смарт-контракт выполняет роль централизованного менеджера поддоменов. Администратор
отвечает за выпуск поддоменов и настройку их DNS-записей.

**Основные особенности:**

* Подходит для простых сценариев
* Быстрая и лёгкая настройка
* Централизованное управление через один смарт-контракт

## Настройка окружения

В этом руководстве используется **Python** совместно с библиотекой с открытым исходным кодом **tonutils**.

### Необходимые компоненты

* **Python 3.10+**
* Зарегистрированный **домен .ton**:
    * Mainnet: [dns.ton.org](https://dns.ton.org)
    * Testnet: [dns.ton.org?testnet=true](https://dns.ton.org?testnet=true)

### Установка зависимостей

Установите необходимую Python-библиотеку:

```bash
pip install tonutils
```

## Менеджер поддоменов

### Развёртывание менеджера

Ниже приведён пример того, как развернуть Менеджер поддоменов с помощью библиотеки tonutils на Python. Этот скрипт
инициализирует смарт-контракт, привязывает его к основному домену и отправляет необходимые транзакции от вашего
кошелька.

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

### Установка записей

Вы можете установить один из следующих типов записей для поддомена. Ниже приведены примеры для каждого случая.

<details>
  <summary><strong>Установить Wallet запись</strong></summary>

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
  <summary><strong>Установить Site запись</strong></summary>

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
  <summary><strong>Установить Storage запись</strong></summary>

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
  <summary><strong>Установить Next Resolver запись</strong></summary>

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

### Удаление записей

Аналогично, вы можете удалять существующие записи. Ниже приведены примеры для каждого типа.

<details>
  <summary>Удалить Wallet запись</summary>

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
  <summary><strong>Удалить Site запись</strong></summary>

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
  <summary><strong>Удалить Storage запись</strong></summary>

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
  <summary><strong>Удалить Next Resolver запись</strong></summary>

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

См. Также
---------

* [Subdomain Manager Contract](https://github.com/Gusarich/simple-subdomain)
