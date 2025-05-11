## Введение

Это руководство объясняет, как создать **красивые (vanity) адреса** в блокчейне TON — контракты или кошельки с заданным шаблоном (например, определёнными начальными или конечными символами), которые делают адрес визуально узнаваемым. Такие адреса часто используются для брендинга, лучшей читаемости или просто эстетики.

---

## Красивый адрес контракта

Чтобы создать **красивый адрес контракта** (например, для Jetton Master-контракта), выполните следующие шаги.

### Клонируйте репозиторий

```bash
git clone https://github.com/ton-community/vanity-contract
```

### Установите зависимости

```bash
pip install -r requirements.txt
```

### Запустите генератор

```bash
python src/generator/run.py --end {suffix} -w -0 --case-sensitive {owner_address}
```

- Замените `{suffix}` на желаемое окончание для генерируемого адреса.
- Замените `{owner_address}` на адрес кошелька, с которого будет выполняться развертывание.

**Пример:**

```bash
python src/generator/run.py --end NESS -w -0 --case-sensitive UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness
```

Если совпадение будет найдено, вы увидите сообщение вроде:

```
Found: EQC7PA9iWnUVWv001Drj3vTu-pmAkTc30OarHy5iDJ1uNESS salt: 7c9398f0999a96fe5480b5d573817255d53377a000be18d0fb47d090a5606dfe
```

### Развёртывание контракта

Скопируйте значение `salt` и вставьте его в константу `SALT` в скрипте развертывания:

```python
--8<-- "examples/vanity/deploy_contract.py"
```

---

## Красивый адрес кошелька

Чтобы создать **красивый адрес кошелька** с использованием ускорения на GPU, выполните следующие шаги.

### Проверьте требования

Требуется видеокарта NVIDIA с установленным драйвером версии 555.* или выше.

### Скачайте бинарник

Скачайте исполняемый файл `gpu-generator-linux` с [последнего релиза](https://github.com/ton-offline-storage/address-generator/releases).

### Запуск генератора

Чтобы запустить генератор в интерактивном режиме:

```bash
./gpu-generator-linux
```

Чтобы запустить генерацию с заранее заданными условиями напрямую из командной строки:

```bash
./gpu-generator-linux -q "start[*][T][O][N] | end[1][2][3]"
```

Следуйте инструкциям на экране, чтобы отслеживать прогресс и просматривать результаты.

После успешного совпадения инструмент выведет **мнемоническую фразу** и **ID кошелька** для использования с кошельком типа `WalletV3R2`.

**Синтаксис ограничений**

* **Допустимые символы**: `A-Z`, `a-z`, `0-9`, `_`, `-`

* **Ограничение по началу** (после префикса `UQ`, третий символ):

    Пример → `start[A][P][P][L][E]` или `start[*][T][O][N]`

* **Ограничение по окончанию**:

    Пример → `end[T][O][N]` или `end[Tt][Oo][Nn]`

* **Комбинированные ограничения**:

    Пример → `start[*][T][O][N] & end[T][O][N]`

* **Несколько вариантов (ИЛИ)**:

    Пример → `start[*][T][O][N] & end[T][O][N] | start[D][D][D] | end[0][0][0]`

**Ориентировочная производительность**

| Hardware              | 5 chars | 6 chars  | 7 chars   | 8 chars   |
|-----------------------|---------|----------|-----------|-----------|
| Intel i5-8350U        | 4 min   | 4 h 40 m | 12.5 days | > 2 years |
| AMD Ryzen 5 3600      | 26 sec  | 30 min   | 31.5 h    | 84 days   |
| NVIDIA GTX 1650 SUPER | 2 sec   | 2 min    | 2 h       | 5.5 days  |
| NVIDIA RTX 4090       | <1 sec  | 13 sec   | 13.5 min  | 14.5 h    |

### Использование сгенерированного кошелька

После получения мнемонической фразы и ID кошелька используйте следующий код:

```python
from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Wallet ID
WALLET_ID = 0


def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC, WALLET_ID)

    print(f"Address: {wallet.address.to_str()}")


if __name__ == "__main__":
    main()
```

Заключение
----------

Красивые (vanity) адреса — это визуальная особенность, позволяющая выделить ваш кошелёк или контракт в сети TON. Хотя они не дают функциональных преимуществ, такие адреса могут быть полезны для брендинга, маркетинга или личной эстетики.

См. Также
---------

- [Vanity Contract Generator](https://github.com/ton-community/vanity-contract)
- [Vanity Wallet Generator](https://github.com/ton-offline-storage/address-generator)
