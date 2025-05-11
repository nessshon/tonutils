Существует несколько способов получить адрес Jetton-кошелька.

---

### Стандартный Jetton

#### Через get-метод

```python
from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStandard


async def main() -> None:
    client = ToncenterV3Client()
    owner_address = "UQ..."
    jetton_master_address = "EQ..."

    wallet_address = await JettonMasterStandard.get_wallet_address(
        client,
        owner_address,
        jetton_master_address,
    )
    print(wallet_address.to_str())

    
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

#### Локальный расчёт

!!! note
    Подготовьте код контракта Jetton Wallet, следуя инструкции из раздела [Получение кода и данных контракта](get-contract-code-and-data.md).

```python
from tonutils.jetton import JettonMasterStandard


def main() -> None:
    owner_address = "UQ..."
    jetton_wallet_code = "..."
    jetton_master_address = "EQ..."

    wallet_address = JettonMasterStandard.calculate_user_jetton_wallet_address(
        owner_address,
        jetton_wallet_code,
        jetton_master_address,
    )
    print(wallet_address.to_str())

    
if __name__ == "__main__":
    main()
```

---

### Stablecoin Jetton

например, USD₮, NOT

#### Через get-метод

```python
from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStablecoin


async def main() -> None:
    client = ToncenterV3Client()
    owner_address = "UQ..."
    jetton_master_address = "EQ..."

    wallet_address = await JettonMasterStablecoin.get_wallet_address(
        client,
        owner_address,
        jetton_master_address,
    )
    print(wallet_address.to_str())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

#### Локальный расчёт

!!! note
    Подготовьте код контракта Jetton Wallet, следуя инструкции из раздела [Получение кода и данных контракта](get-contract-code-and-data.md).

```python
from tonutils.jetton import JettonMasterStablecoin


def main() -> None:
    owner_address = "UQ..."
    jetton_wallet_code = "..."
    jetton_master_address = "EQ..."

    wallet_address = JettonMasterStablecoin.calculate_user_jetton_wallet_address(
        owner_address,
        jetton_wallet_code,
        jetton_master_address,
    )
    print(wallet_address.to_str())


if __name__ == "__main__":
    main()
```
