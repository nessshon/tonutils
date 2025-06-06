В этом разделе приведены практические примеры работы с библиотекой `tonutils`. Вы узнаете, как создавать и импортировать кошельки, отправлять транзакции, получать информацию о контрактах и выполнять их методы в сети TON.

---

## Работа с кошельком

### Создание кошелька

```python
from tonutils.wallet import WalletV4R2
from tonutils.client import ToncenterV3Client

client = ToncenterV3Client(is_testnet=True, rps=1)
wallet, public_key, private_key, mnemonic = WalletV4R2.create(client)
```

**Результат:**

- `wallet`: экземпляр `WalletV4R2`, готовый к использованию
- `public_key`: байтовое представление публичного ключа (`bytes`)
- `private_key`: байтовое представление приватного ключа (`bytes`)
- `mnemonic`: список из 24 слов (`List[str]`)

---

### Импорт кошелька

```python
wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)
```

**Параметр:**

- `MNEMONIC` — может быть указан в одном из двух форматов:
    - строка из 12/24 слов, разделённых пробелами;
    - список из 12/24 слов.

---

## Отправка транзакций

### Одиночная транзакция

```python
tx_hash = await wallet.transfer(
    destination="nessshon.t.me",
    amount=1,
    body="Hello from tonutils!",
)
```

**Параметры:**

- `destination`: получатель — может быть:
    - строкой с адресом;
    - объектом `Address`;
    - доменным именем `.ton` или `.t.me`;
- `amount`: сумма перевода в TON (не в nanotons);
- `body`: комментарий в виде строки или произвольные данные в виде объекта `Cell`.

**Результат:**

- Нормализованный хэш сообщения (`str`)

---

### Пакетная отправка

Позволяет отправить несколько переводов в рамках одной транзакции:

```python
from tonutils.wallet.messages import TransferMessage

tx_hash = await wallet.batch_transfer_messages([
    TransferMessage(destination="UQ...", amount=0.01, body="Hello from tonutils!"),
    TransferMessage(destination="UQ...", amount=0.02, body="Hello from tonutils!"),
])
```

**Результат:**

- Нормализованный хэш сообщения (`str`)

---

### Режим отправки

Параметр `send_mode` управляет поведением транзакции — позволяет, например, отправить весь баланс (`128`)

```python
await wallet.transfer(
    destination="UQ...",
    amount=0,
    send_mode=128,
)
```

!!! note
    Подробнее о доступных режимах см. в [официальной документации TON](https://docs.ton.org/v3/documentation/smart-contracts/message-management/message-modes-cookbook).

---

## Информация о контракте

### Баланс контракта

```python
balance = await client.get_account_balance("UQ...")
```

**Результат:**

Целое число (`int`), представляющее баланс контракта в nanotons.

---

### Данные контракта

```python
contract_data = await client.get_raw_account("UQ...")
```

**Результат:**

Объект с информацией о контракте, содержащий следующие поля:

- `balance`: текущий баланс контракта в nanotons (`int`);
- `status`: состояние аккаунта: `active`, `nonexist`, `frozen`, `uninit`;
- `code`: код контракта (`Optional[Cell]`);
- `data`: данные контракта (`Optional[Cell]`);
- `last_transaction_lt`: логическое время последней транзакции (`Optional[int]`);
- `last_transaction_hash`: хэш последней транзакции (`Optional[str]`);
- `state_init`: объект `StateInit`, если заданы `code` и `data`.

---

## Вызов метода контракта

Метод `run_get_method` позволяет выполнить вызов `get-method` контракта.

```python
result = await client.run_get_method(
    address="UQ...",
    method_name="get_my_data",
    stack=[0]
)
```

**Параметры:**

- `address`: строка с адресом контракта;
- `method_name`: имя вызываемого метода (`str`);
- `stack`: список аргументов (допустимые типы: `int`, `Cell`, `Slice`).

**Результат:**

Список значений, возвращённых из стека после выполнения метода.
