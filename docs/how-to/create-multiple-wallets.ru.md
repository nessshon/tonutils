Этот пример демонстрирует, как сгенерировать **несколько адресов кошельков** из одной мнемонической фразы путём изменения значения `subwallet_id`.
Каждое значение `subwallet_id` создаёт уникальный адрес на основе одной и той же seed-фразы.

---

### Пример

```python
from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Subwallet ID
WALLET_ID = 0


def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC, WALLET_ID)

    print(f"Address: {wallet.address.to_str()}")


if __name__ == "__main__":
    main()
```

---

### Пояснение

* **`subwallet_id`** → 32-битное целое число, используемое для получения разных адресов кошельков из одной и той же мнемоники.
* **Примеры использования**:

    * Разделение средств по логическим аккаунтам.
    * Управление раздельными балансами.
    * Создание производных кошельков для работы с контрактами.

---

### Важные замечания

* `subwallet_id` (или `wallet_id`) **не поддерживается** в следующих типах кошельков:

    * `WalletV2*`
    * `PreprocessedWallet*`

* **Значения `wallet_id` по умолчанию**:

    * Все типы кошельков, кроме `WalletV5R1` → `698983191`
    * Для `WalletV5R1`:

        | global_id | workchain | wallet_version | subwallet_number | wallet_id  |
        |-----------|-----------|----------------|------------------|------------|
        | -239      | 0         | 0              | 0                | 2147483409 |
        | -239      | -1        | 0              | 0                | 8388369    |
        | -3        | 0         | 0              | 0                | 2147483645 |
        | -3        | -1        | 0              | 0                | 8388605    |
