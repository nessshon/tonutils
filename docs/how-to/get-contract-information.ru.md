Этот пример демонстрирует, как получить полную информацию о контракте, включая баланс, статус, код, данные и метаданные последней транзакции.

---

### Пример
```python
from tonutils.client import ToncenterV3Client


async def main() -> None:
    client = ToncenterV3Client()
    contract_address = "EQ..."

    contract = await client.get_raw_account(contract_address)

    print(f"Balance: {contract.balance}")
    print(f"Status: {contract.status}")
    print(f"Code: {contract.code}")
    print(f"Data: {contract.data}")
    print(f"Last Transaction LT: {contract.last_transaction_lt}")
    print(f"Last Transaction Hash: {contract.last_transaction_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

---

### Обзор полей `RawAccount`

* **balance** → целое число (в nanoTON)  
  Текущий баланс контракта.

* **status** → строка  
  Статус контракта, возможные значения:
    * `active` → контракт существует и активен
    * `nonexist` → контракт не существует
    * `frozen` → контракт заморожен
    * `uninit` → контракт существует, но не инициализирован

* **code** → `Cell` (опционально)  
  Исполняемый код контракта (если есть).

* **data** → `Cell` (опционально)  
  Персистентные данные контракта (если есть).

* **last_transaction_lt** → целое число (опционально)  
  Логическое время (LT) последней транзакции.

* **last_transaction_hash** → строка (опционально)  
  Хеш последней транзакции.

* **state_init** → `StateInit` (опционально)  
  Объединённый объект, представляющий полное состояние контракта, если доступны и код, и данные.
