## Введение

Это руководство проведёт вас через процесс создания и управления **поддоменами в блокчейне TON** с использованием инструментов с открытым исходным кодом. Оно охватывает развертывание контрактов управления поддоменами, выпуск поддоменов и управление DNS-записями с практическими примерами.

## Реализация

Существует две реализации с открытым исходным кодом для управления поддоменами в TON, выбор зависит от требуемого уровня сложности и контроля:

### Коллекция поддоменов

[GitHub ↗](https://github.com/nessshon/subdomains-toolbox/tree/main/collection-contracts/admin-mint)

Это более продвинутое решение, в котором каждый поддомен представлен в виде NFT. Владелец коллекции отвечает за выпуск поддоменов, а каждый владелец NFT получает полный контроль над своим поддоменом.

**Основные особенности:**

* Поддомены можно передавать и продавать
* Децентрализованное управление записями — у каждого поддомена свой смарт-контракт
* Требует дополнительной инфраструктуры (например, API для метаданных)

### Менеджер поддоменов

[GitHub ↗](https://github.com/Gusarich/simple-subdomain)

Это базовая реализация, где один смарт-контракт выполняет роль централизованного менеджера поддоменов. Администратор отвечает за выпуск поддоменов и настройку их DNS-записей.

**Основные особенности:**

* Подходит для простых сценариев
* Быстрая и лёгкая настройка
* Централизованное управление через один смарт-контракт

## Настройка окружения

В этом руководстве используется **Python** совместно с библиотекой с открытым исходным кодом **tonutils**, которая поддерживает обе реализации управления поддоменами.

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

### Дополнительные требования для коллекции поддоменов

Если вы используете подход с коллекцией поддоменов, вам также понадобятся:

* Сервер для размещения **API метаданных**
* **Доменное имя**, указывающее на этот сервер, для доступа к метаданным
* Установленные **Docker** и **Docker Compose** для развертывания API

## Коллекция поддоменов

### Настройка метаданных

Перед развертыванием коллекции поддоменов необходимо запустить API метаданных. Этот сервис отвечает за генерацию динамических изображений и атрибутов для ваших NFT-поддоменов, делая их визуально распознаваемыми.

1. Клонируйте репозиторий:  

     ```bash
     git clone https://github.com/nessshon/subdomains-toolbox
     cd metadata-api
     ```

2. Запустите API с помощью Docker:  
   API будет работать на порту `8001`. Необходимо настроить SSL и обратный прокси для безопасного доступа.

     ```bash
     docker-compose up -d
     ```

3. Проверьте работу API:  
   Откройте в браузере `https://your-domain.com/api/ton/example.png`. При корректной настройке вы увидите сгенерированное изображение для поддомена `example`.

### Развертывание коллекции

После запуска API вы можете развернуть смарт-контракт NFT коллекции для ваших поддоменов.

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns import DNS
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
                body=DNS.build_set_next_resolver_record_body(collection.address),
            ),
        ]
    )

    print(f"Successfully deployed Subdomain Collection at address: {collection.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Выпуск поддоменов

Чтобы выпустить новый поддомен в виде NFT:

1. Откройте свой TON-кошелёк (например, Tonkeeper).
2. Отправьте **0.1 TON** на адрес контракта коллекции поддоменов (он отображается при развертывании).
3. В поле комментария к транзакции укажите желаемое имя поддомена (например, `alice` для `alice.ghost.ton`).
4. Убедитесь, что имя поддомена корректно (только латинские буквы и цифры, без специальных символов) и ещё не занято.
5. После подтверждения транзакции NFT поддомен будет отправлен в ваш кошелёк.

### Управление записями

#### Установка записей

Механизм установки записей для NFT поддоменов аналогичен тому, что используется в коллекции **TON DNS Domains**. Вы можете назначить поддомену одну из следующих типов записей — ниже приведены примеры для каждого случая.

<details>
  <summary><strong>Установить Wallet запись</strong></summary>

```python
import asyncio
from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_set_wallet_record_body(Address(WALLET_ADDRESS))

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
  <summary><strong>Установить Site запись</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_set_site_record_body(ADNL_ADDRESS)

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
  <summary><strong>Установить Storage запись</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_set_storage_record_body(BAG_ID)

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
  <summary><strong>Установить Next Resolver запись</strong></summary>

```python
import asyncio

from pytoniq_core import Address
from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_set_next_resolver_record_body(Address(CONTRACT_ADDRESS))

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

#### Удаление записей

Аналогично, вы можете удалять уже существующие записи. Ниже приведены примеры для каждого типа.

<details>
  <summary><strong>Удалить Wallet запись</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_delete_wallet_record_body()

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
  <summary><strong>Удалить Site запись</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_delete_site_record_body()

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
  <summary><strong>Удалить Storage запись</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_delete_storage_record_body()

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
  <summary><strong>Удалить Next Resolver запись</strong></summary>

```python
import asyncio

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
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

    body = DNS.build_delete_next_resolver_record_body()

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

## Менеджер поддоменов

### Развёртывание менеджера

Ниже приведён пример того, как развернуть Менеджер поддоменов с помощью библиотеки tonutils на Python. Этот скрипт инициализирует смарт-контракт, привязывает его к основному домену и отправляет необходимые транзакции от вашего кошелька.

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

Заключение
----------

Блокчейн TON предлагает гибкие варианты управления поддоменами — будь то централизованный подход с использованием Менеджера поддоменов или децентрализованное решение на основе NFT с Коллекцией поддоменов. Обе схемы легко реализуются и предоставляют мощные инструменты для эффективного управления поддоменами и DNS-записями. Это руководство включает все необходимые шаги для начала работы и полного контроля над вашими поддоменами в TON.

См. Также
---------

* [TON Subdomains Toolbox](https://github.com/nessshon/subdomains-toolbox)
* [Subdomain Manager Contract](https://github.com/Gusarich/simple-subdomain)
* [Subdomain Collection Contract](https://github.com/nessshon/subdomains-toolbox/tree/main/collection-contracts/admin-mint)
