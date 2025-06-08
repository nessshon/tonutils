## Введение

Это руководство объясняет, как интегрировать TON Connect в Python-приложения с использованием библиотеки `tonutils` — высокоуровневого SDK, разработанного для удобного взаимодействия с TON. В нём рассматриваются инициализация подключения, аутентификация кошельков, отправка транзакций и подпись данных, обеспечивая практическую основу для создания безопасных dApp-приложений с поддержкой кошельков в сети TON.

## Реализация

### Установка

```bash
pip install tonutils
```

Для хранения данных о подключениях кошельков пользователей необходимо реализовать интерфейс хранилища. Для этого требуется дополнительная зависимость. В данном примере используется реализация на основе файла с использованием `aiofiles`:

```bash
pip install aiofiles
```

### Создание Manifest

Создайте файл `manifest.json` для вашего приложения в соответствии с [инструкцией](https://docs.ton.org/v3/guidelines/ton-connect/guidelines/creating-manifest) и разместите его по публично доступному URL.

### Реализация хранилища

Для хранения данных о соединениях с пользовательскими кошельками необходимо реализовать интерфейс хранилища.

<details>
  <summary><b>Пример реализации</b></summary>

```python
import json
import os
from asyncio import Lock
from typing import Dict, Optional

import aiofiles

from tonutils.tonconnect import IStorage


class FileStorage(IStorage):

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = Lock()

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump({}, f)  # type: ignore

    async def _read_data(self) -> Dict[str, str]:
        async with self.lock:
            async with aiofiles.open(self.file_path, "r") as f:
                content = await f.read()
                if content:
                    return json.loads(content)
                return {}

    async def _write_data(self, data: Dict[str, str]) -> None:
        async with self.lock:
            async with aiofiles.open(self.file_path, "w") as f:
                await f.write(json.dumps(data, indent=4))

    async def set_item(self, key: str, value: str) -> None:
        data = await self._read_data()
        data[key] = value
        await self._write_data(data)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        data = await self._read_data()
        return data.get(key, default_value)

    async def remove_item(self, key: str) -> None:
        data = await self._read_data()
        if key in data:
            del data[key]
            await self._write_data(data)
```

</details>

### Инициализация TON Connect

Создайте экземпляр `TonConnect`, указав URL манифеста и объект хранилища:

```python
from storage import FileStorage
from tonutils.tonconnect import TonConnect

TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"
TC_STORAGE = FileStorage("connection.json")

tc = TonConnect(
    storage=TC_STORAGE,
    manifest_url=TC_MANIFEST_URL,
    wallets_fallback_file_path="./wallets.json"
)
```

Параметр `wallets_fallback_file_path` используется как резервный источник данных о кошельках (например, Tonkeeper, Wallet) в случае недоступности внешнего API.
Со всеми входными параметрами можно ознакомиться по следующей [ссылке](https://github.com/nessshon/tonutils/blob/main/tonutils/tonconnect/tonconnect.py#L40).

### Инициализация Connector

Создайте экземпляр `Connector` для работы с конкретным пользователем:

```python
connector = await tc.init_connector(user_id)
```

* `user_id` может быть целым числом (`int`) или строкой (`str`).
* Если не указан, будет автоматически присвоен инкрементный идентификатор.
* Вы можете сохранить `user_id` для последующего использования:

  ```python
  user_id = connector.user_id
  ```

## Подключение кошелька

### Получение списка кошельков

Чтобы отобразить доступные кошельки в пользовательском интерфейсе, получите список поддерживаемых кошельков:

```python
wallets = await tc.get_wallets()
```

Затем вам нужно отобразить список, используя например имя каждого кошелька через `wallet.name`.

### Подключение к кошельку

После того как пользователь выберет кошелек из списка, инициируйте подключение (для примера, выберем кошелек с индексом 1):

```python
selected_wallet = wallets[1]
connect_url = await connector.connect_wallet(selected_wallet)
```

Вы должны отобразить `connect_url` пользователю в вашем приложении.

#### С использованием Redirect URL

Если вы хотите автоматически перенаправить пользователя после успешного подключения, передайте параметр `redirect_url`:

```python
redirect_url = "https://example.com/"
connect_url = await connector.connect_wallet(selected_wallet, redirect_url=redirect_url)
```

#### С использованием TON Proof

Чтобы убедиться, что пользователь действительно владеет указанным адресом, вы можете включить проверку владения адресом с помощью `ton_proof`.
Сгенерируйте полезную нагрузку (payload) для проверки и передайте её через параметр `ton_proof`.
Подробнее о механизме и генерации payload можно узнать [здесь](https://docs.ton.org/v3/guidelines/ton-connect/guidelines/verifying-signed-in-users).

Вы также можете использовать встроенную функцию `generate_proof_payload` из `tonutils`:

```python
from tonutils.tonconnect.utils import generate_proof_payload

redirect_url = "https://example.com/"
proof_payload = generate_proof_payload()
connect_url = await connector.connect_wallet(
    selected_wallet,
    redirect_url=redirect_url,
    ton_proof=proof_payload
)
```

### Обработка подключения

Для обработки результата подключения кошелька используйте контекстный менеджер `connect_wallet_context`.

**Пример использования контекстного менеджера:**

```python
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError

async with connector.connect_wallet_context() as response:
    if isinstance(response, TonConnectError):
        if isinstance(response, UserRejectsError):
            print("The user rejected the connection.")
        else:
            print(f"Connection error: {response.message}")
    else:
        print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
```

**Пример с проверкой `ton_proof`:**

```python
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError

async with connector.connect_wallet_context() as response:
    if isinstance(response, TonConnectError):
        if isinstance(response, UserRejectsError):
            print("The user rejected the connection.")
        else:
            print(f"Connection error: {response.message}")
    else:
        if connector.wallet.verify_proof_payload(proof_payload):
            print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
        else:
            await connector.disconnect_wallet()
            print("Proof verification failed.")
```

Контекстный менеджер приостанавливает выполнение до тех пор, пока:

* пользователь не подключит кошелёк;
* не произойдёт тайм-аут;
* или не произойдёт ошибка.

В случае успеха вы получите объект [WalletInfo](https://github.com/nessshon/tonutils/blob/main/tonutils/tonconnect/models/wallet.py#L118), содержащий данные подключенного кошелька.
В случае ошибки будет возвращён экземпляр `TonConnectError`, который можно обработать, как описано в разделе [обработка ошибок](#_36).

## Отправка запросов

### Отправка транзакции

Чтобы отправить Toncoin на определённый адрес, используйте метод `send_transaction`:

```python
from tonutils.tonconnect.models import Transaction, Message

rpc_request_id = await connector.send_transaction(
    transaction=Transaction(
        valid_until=int(time.time() + 5 * 60),
        messages=[
            Message(
                address="UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness",
                amount=str(int(1 * 1e9)),
            )
        ]
    )
)
```

* `valid_until` – время истечения транзакции в секундах
* `address` – получатель в user-friendly формате
* `amount` – сумма в нанотонах

Метод возвращает `rpc_request_id` — уникальный идентификатор для отслеживания запроса.

### Упрощённая отправка транзакции

Библиотека `tonutils` также предоставляет более удобные высокоуровневые методы для отправки транзакций.

* Поле `valid_until` по умолчанию равна 5 минут.
* Поле `address` заменено на `destination` (строка или объект `Address`).
* Сумма указывается в **TON**, а не в **нанотонах**.
* Параметр `body` может быть:

  * объектом `Cell` — для передачи пользовательских данных;
  * строкой — используется как комментарий или мемо;

#### Одиночный перевод

```python
rpc_request_id = await connector.send_transfer(
    destination="UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness",
    amount=1,
    body="Hello from tonutils!",
)
```

#### Пакетная отправка

Прежде чем отправлять несколько сообщений в одной транзакции, убедитесь, что кошелёк поддерживает необходимое количество сообщений:

```python
max_messages = connector.device.get_max_supported_messages(connector.wallet)
```

Максимальное количество сообщений в одной транзакции зависит от версии кошелька.
Учитывайте это ограничение при построении логики отправки транзакции.

```python
from tonutils.tonconnect.models.transfer import TransferMessage

rpc_request_id = await connector.send_batch_transfer(
    messages=[
        TransferMessage(
            destination="UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness",
            amount=1,
            body="Hello from tonutils!",
        ),
        TransferMessage(
            destination="UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness",
            amount=2,
            body="Hello from tonutils!",
        ),
    ]
)
```

Эти методы также возвращают `rpc_request_id`.

### Отправка запроса на подпись данных

Метод `sign_data` позволяет запросить криптографическую подпись произвольного содержимого от кошелька пользователя.
Эта подпись подтверждает явное согласие и может быть проверена вне блокчейна или передана в смарт-контракт.

TON Connect поддерживает три формата данных:

#### Текст

Используется, когда содержимое предназначено для прочтения человеком.

* Понятно пользователю.
* Идеально подходит для подтверждений вне блокчейна.

```python
from tonutils.tonconnect.models import SignDataPayloadText

text = "I confirm deletion of my account and all associated data."
payload = SignDataPayloadText(text=text)
```

#### Бинарный

Используется для хэшей, файлов или нечитаемого содержимого.

* Подходит для цифровых квитанций, доказательств или непрозрачных данных.

```python
from tonutils.tonconnect.models import SignDataPayloadBinary

data = "I confirm deletion of my account and all associated data.".encode("utf-8")
payload = SignDataPayloadBinary(bytes=data)
```

#### Ячейка

Используется, когда подпись должна быть проверяема на блокчейне.

* Поддерживает TL-B схемы.
* Позволяет проводить проверку в смарт-контракте.

```python
from pytoniq_core import begin_cell
from tonutils.tonconnect.models import SignDataPayloadCell

comment = "I confirm deletion of my account and all associated data."
cell = begin_cell().store_uint(0, 32).store_snake_string(comment).end_cell()
schema = "text_comment#00000000 text:Snakedata = InMsgBody;"

payload = SignDataPayloadCell(cell=cell, schema=schema)
```

Последний тип в предоставленной TL-B схеме используется в качестве корневого типа для сериализации.

#### Отправка запроса

Прежде чем отправить запрос, необходимо убедиться, что подключённый кошелёк поддерживает функцию подписи данных.
Используйте следующую проверку:

```python
connector.device.verify_sign_data_feature(connector.wallet, payload)
```

Если функция не поддерживается, будет вызвано исключение `WalletNotSupportFeatureError`.
Вы можете обработать его следующим образом:

```python
from tonutils.tonconnect.utils.exceptions import WalletNotSupportFeatureError

try:
    connector.device.verify_sign_data_feature(connector.wallet, payload)
except WalletNotSupportFeatureError:
    print("Wallet does not support sign data feature!")
    # Handle fallback logic or abort
```

Если функция поддерживается, продолжайте отправку запроса:

```python
rpc_request_id = await connector.sign_data(payload)
```

### Обработка результатов запроса

Для ожидания ответа пользователя на транзакцию или запрос подписи используйте контекстный менеджер `pending_request_context`.

Контекстный менеджер приостанавливает выполнение до тех пор, пока:

* пользователь не выполнит действие в своём кошельке;
* не произойдёт тайм-аут;
* или не произойдёт ошибка.

В случае успеха возвращается объект ответа, соответствующий типу запроса:

* [`SendTransactionResponse`](https://github.com/nessshon/tonutils/blob/main/tonutils/tonconnect/models/requests.py#L244)
* [`SignDataResponse`](https://github.com/nessshon/tonutils/blob/main/tonutils/tonconnect/models/requests.py#L493)

В случае ошибки возвращается `TonConnectError`, который можно обработать, как описано в разделе [ошибки запроса](#_37).

#### Обработка подписанных данных

```python
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError

async with connector.pending_request_context(rpc_request_id) as response:
    if isinstance(response, TonConnectError):
        if isinstance(response, UserRejectsError):
            print("The user rejected the signing request.")
        else:
            print(f"Sign data error: {response.message}")
    else:
        key = connector.wallet.account.public_key
        if response.verify_sign_data(key):
            print("Verified sign data!")
        else:
            print("Failed to verify sign data!")
```

#### Обработка транзакции

```python
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError

async with connector.pending_request_context(rpc_request_id) as response:
    if isinstance(response, TonConnectError):
        if isinstance(response, UserRejectsError):
            print("The user rejected the transaction.")
        else:
            print(f"Transaction error: {response.message}")
    else:
        print(f"Transaction sent successfully! Hash: {response.normalized_hash}")
```

### Проверка статуса запроса

Чтобы проверить, ожидает ли запрос подтверждения от пользователя:

```python
is_pending = connector.is_request_pending(rpc_request_id)
```

Этот метод возвращает `True`, если запрос ещё не был подтверждён в кошельке пользователя; в противном случае возвращается `False`.

### Отмена запроса

Если необходимо отменить запрос по какой-либо причине, используйте:

```python
connector.cancel_pending_request(rpc_request_id)
```

Это полностью останавливает обработку запроса на уровне приложения, даже если пользователь позже подтвердит его в кошельке.

## Отключение кошелька

Чтобы отключить кошелёк пользователя, вызовите метод `disconnect_wallet`:

```python
await connector.disconnect_wallet()
```

## Обработка событий

Помимо контекстных менеджеров, **tonutils** предоставляет единый событийно-ориентированный интерфейс для реагирования на действия кошелька.
Это позволяет обрабатывать события, такие как подключение и отключение кошелька, выполнение транзакций и подписание данных, с помощью зарегистрированных обработчиков.

### Типы событий

TON Connect генерирует два типа событий:

#### Успешные события

Эти события срабатывают при успешном завершении действия:

* `Event.CONNECT` — кошелёк успешно подключён.  
  **Параметры:** `user_id: int`, `wallet: WalletInfo`

* `Event.DISCONNECT` — кошелёк отключён.  
  **Параметры:** `user_id: int`, `wallet: WalletInfo`

* `Event.TRANSACTION` — пользователь подтвердил транзакцию.  
  **Параметры:** `user_id: int`, `transaction: SendTransactionResponse`, `rpc_request_id: int`

* `Event.SIGN_DATA` — пользователь одобрил запрос на подписание данных.  
  **Параметры:** `user_id: int`, `sign_data: SignDataResponse`, `rpc_request_id: int`

#### События ошибок

Эти события срабатывают **в случае сбоя действия** — из-за отказа пользователя, тайм-аута или ошибки внутри кошелька/приложения:

* `EventError.CONNECT` — ошибка при подключении кошелька.
* `EventError.DISCONNECT` — ошибка при отключении кошелька.
* `EventError.TRANSACTION` — ошибка при подтверждении транзакции.
* `EventError.SIGN_DATA` — ошибка при подписании данных.

  **Все события ошибок содержат:**

  * `user_id: int`
  * `error: TonConnectError`

  **Примечание:** Все типы ошибок подробно описаны в разделе [обработка ошибок](#_35).

Вы можете обрабатывать эти ошибки так же, как обычные события, используя `register_event` или декораторы.
Такое разделение позволяет чётко отделять логику обработки успеха и ошибок.

### Обработка событий

Вы можете зарегистрировать обработчики событий двумя способами:

#### С помощью метода

```python
def on_transaction(user_id: int, transaction: SendTransactionResponse):
    print(f"Transaction received for user {user_id}")

tc.register_event(Event.TRANSACTION, on_transaction)
```

#### С использованием декораторов

```python
@tc.on_event(Event.TRANSACTION)
async def on_transaction(user_id: int, transaction: SendTransactionResponse):
    print(f"Transaction confirmed for user {user_id}")
```

### Дополнительные параметры

Помимо стандартных аргументов событий, вы можете передавать пользовательские параметры (например, сессию базы данных, объекты контекста, комментарии) в обработчики событий.

#### Привязка параметров к конкретному событию:

Вызовите `add_event_kwargs` до входа в контекстный менеджер или запуска запроса:

```python
connector.add_event_kwargs(
    event=Event.CONNECT,
    comment="Hello from tonutils!",
    db_session=session,
)
```

Дополнительные именованные аргументы будут переданы напрямую в соответствующий обработчик:

```python
@tc.on_event(Event.CONNECT)
async def on_connect(user_id: int, wallet: WalletInfo, comment: str, db_session: Session):
    ...
```

#### Определение глобальных параметров для всех событий:

Вы можете задать параметры по умолчанию для всех событий на уровне `connector`:

```python
tc = TonConnect(
    storage=TC_STORAGE,
    manifest_url=TC_MANIFEST_URL,
    wallets_fallback_file_path="./wallets.json"
)
tc["db_session"] = session
tc["comment"] = "Shared message"
```

Эти параметры будут доступны во **всех** обработчиках событий:

```python
@tc.on_event(Event.SIGN_DATA)
async def on_sign_data(user_id: int, sign_data: SignDataResponse, db_session: Session, comment: str):
    ...
```

## Обработка ошибок

При работе с TON Connect могут возникать ошибки как во время подключения кошелька, так и при отправке запросов.

### Ошибки подключения

Эти ошибки могут возникнуть на этапе инициализации подключения к кошельку:

| Код  | Ошибка                    | Описание                                                                |
|------|---------------------------|-------------------------------------------------------------------------|
| 0    | `UnknownError`            | Неизвестная ошибка в кошельке при обработке запроса.                    |
| 1    | `BadRequestError`         | Запрос некорректен или содержит недопустимые параметры.                 |
| 2    | `ManifestNotFoundError`   | Указанный `manifest_url` недоступен или не существует.                  |
| 3    | `ManifestContentError`    | Содержимое манифеста имеет некорректную структуру или форматирование.   |
| 100  | `UnknownAppError`         | Ошибка логики приложения при подготовке данных запроса.                 |
| 300  | `UserRejectsError`        | Пользователь отказался подключать кошелёк к вашему приложению.          |
| 400  | `MethodNotSupportedError` | Выбранный кошелёк не поддерживает запрашиваемую операцию или метод.     |
| 500  | `RequestTimeoutError`     | Пользователь не завершил подключение в установленный срок.              |

### Ошибки запросов

Эти ошибки могут возникать при обработке запросов.

| Код  | Ошибка                    | Описание                                                              |
|------|---------------------------|-----------------------------------------------------------------------|
| 0    | `UnknownError`            | Неизвестная ошибка в кошельке при обработке запроса.                  |
| 1    | `BadRequestError`         | Запрос некорректен или содержит недопустимые параметры.               |
| 100  | `UnknownAppError`         | Ошибка логики приложения при подготовке данных запроса.               |
| 300  | `UserRejectsError`        | Пользователь отклонил запрос или отказался подписывать данные.        |
| 400  | `MethodNotSupportedError` | Выбранный кошелёк не поддерживает запрашиваемую операцию или метод.   |
| 500  | `RequestTimeoutError`     | Пользователь не подтвердил запрос в установленный срок.               |

## Заключение
-------------

TON Connect предоставляет безопасный и удобный способ взаимодействия с кошельками в сети TON. Благодаря поддержке подписи транзакций, верификации личности и обработки событий, он позволяет легко интегрировать функциональность кошельков в Python-приложения.

## См. Также
------------

* [Примеры использования TON Connect](../guide/examples/ton-connect-operations.md)
* [Telegram-бот с интеграцией TON Connect](../cookbook/tonconnect-telegram.md)
