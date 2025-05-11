Этот раздел объясняет, как установить библиотеку `tonutils` и выбрать подходящий клиент в зависимости от ваших потребностей.

---

## Установка

Чтобы установить базовый пакет `tonutils`:

```bash
pip install tonutils
```

Если вы хотите использовать подключение через [Нативный ADNL](#pytoniq), установите с дополнительными зависимостями:

```bash
pip install 'tonutils[pytoniq]'
```

---

## Доступные клиенты

### RPC API

#### toncenter

**[toncenter.com](https://toncenter.com)** — быстрый и надёжный HTTP API для The Open Network.  

!!! note
    API-ключ не обязателен, но для лучшей производительности рекомендуется получить его через [@tonapibot](https://t.me/tonapibot).

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

**[tonapi.io](https://tonapi.io)** — REST API для работы с обозревателем блокчейна TON.  

!!! note
    Требуется API-ключ с сайта [tonconsole.com](https://tonconsole.com).

```python
from tonutils.client import TonapiClient

API_KEY = "your api key"
IS_TESTNET = True
client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

---

#### quicknode

**[quicknode.com](https://quicknode.com)** — HTTP API с низкой задержкой к TON через глобальную инфраструктуру.  

!!! note
    Требуется URL API с сайта [quicknode.com](https://quicknode.com).

    Quicknode не поддерживает тестовую сеть!

```python
from tonutils.client import QuicknodeClient

HTTP_PROVIDER_URL = "https://blissful-withered-surf.ton-mainnet.quiknode.pro/d6e8...1964"
client = QuicknodeClient(HTTP_PROVIDER_URL)
```

---

#### tatum

**[tatum.io](https://tatum.io)** — RPC и API для Web3.  

!!! note
    Требуется API-ключ с сайта [tatum.io](https://tatum.io).

```python
from tonutils.client import TatumClient

API_KEY = "your api key"
IS_TESTNET = True
client = TatumClient(api_key=API_KEY, is_testnet=IS_TESTNET)
```

---

### Нативный ADNL

#### pytoniq

**[pytoniq](https://github.com/yungwine/pytoniq)** — библиотека для прямого взаимодействия с лайт-серверами.  

!!! note
    Для лучшей производительности рекомендуется указать собственную конфигурацию, которую можно получить через [бота liteserver](https://t.me/liteserver_bot).

```python
from tonutils.client import LiteserverClient

IS_TESTNET = True
client = LiteserverClient(is_testnet=IS_TESTNET)

# Using custom configuration
# config = {}  # Your LiteServer config here 
# client = LiteserverClient(config=config)
```
