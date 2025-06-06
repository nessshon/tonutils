Этот раздел предоставляет полное руководство по работе с Jetton с использованием библиотеки `tonutils`.
Описаны операции как с **Stablecoin Jetton** (by Notcoin), так и со **Standard Jetton**, включая развёртывание, выпуск, сжигание, администрирование и обмен через децентрализованные биржи, такие как **STON.fi** и **DeDust.io**.

---

## Stablecoin Jetton

### Развёртывание Jetton Master

```python
--8<-- "examples/jetton/stablecoin/deploy_master.py"
```

### Обновление контракта

```python
--8<-- "examples/jetton/stablecoin/upgrade_contract.py"
```

### Выпуск Jetton

```python
--8<-- "examples/jetton/stablecoin/mint_jetton.py"
```

### Сжигание Jetton

```python
--8<-- "examples/jetton/stablecoin/burn_jetton.py"
```

### Смена администратора

```python
--8<-- "examples/jetton/stablecoin/change_admin.py"
```

### Удаление администратора

```python
--8<-- "examples/jetton/stablecoin/drop_admin.py"
```

### Изменение контента

```python
--8<-- "examples/jetton/stablecoin/change_content.py"
```

---

## Standard Jetton

### Развёртывание Jetton Master (ончейн)

```python
--8<-- "examples/jetton/standard/deploy_master_onchain.py"
```

### Развёртывание Jetton Master (оффчейн)

```python
--8<-- "examples/jetton/standard/deploy_master_offchain.py"
```

### Выпуск Jetton

```python
--8<-- "examples/jetton/standard/mint_jetton.py"
```

### Сжигание Jetton

```python
--8<-- "examples/jetton/standard/burn_jetton.py"
```

### Смена администратора

```python
--8<-- "examples/jetton/standard/change_admin.py"
```

### Изменение контента

```python
--8<-- "examples/jetton/standard/change_content.py"
```

---

## Обмен Jetton

### Через STON.fi

#### Обмен TON → Jetton

!!! note
    Перед использованием обязательно ознакомьтесь с официальной документацией [STON.fi](https://docs.ston.fi/).
    Используйте с осторожностью и **всегда тестируйте сначала в тестовой сети**.
    Автор не несёт **никакой ответственности** за возможные потери средств.
    Нашли ошибку или есть предложения — создайте pull request.

```python
--8<-- "examples/jetton/dex/stonfi/swap_ton_to_jetton.py"
```

#### Обмен Jetton → TON

!!! note
    Перед использованием обязательно ознакомьтесь с официальной документацией [STON.fi](https://docs.ston.fi/).
    Используйте с осторожностью и **всегда тестируйте сначала в тестовой сети**.
    Автор не несёт **никакой ответственности** за возможные потери средств.
    Нашли ошибку или есть предложения — создайте pull request.

```python
--8<-- "examples/jetton/dex/stonfi/swap_jetton_to_ton.py"
```

#### Обмен Jetton → Jetton

!!! note
    Перед использованием обязательно ознакомьтесь с официальной документацией [STON.fi](https://docs.ston.fi/).
    Используйте с осторожностью и **всегда тестируйте сначала в тестовой сети**.
    Автор не несёт **никакой ответственности** за возможные потери средств.
    Нашли ошибку или есть предложения — создайте pull request.

```python
--8<-- "examples/jetton/dex/stonfi/swap_jetton_to_jetton.py"
```

### Через DeDust.io

#### Обмен TON → Jetton

!!! note
    Перед использованием обязательно ознакомьтесь с официальной документацией [DeDust.io](https://docs.dedust.io/docs/introduction).
    Используйте с осторожностью и **всегда тестируйте сначала в тестовой сети**.
    Автор не несёт **никакой ответственности** за возможные потери средств.
    Нашли ошибку или есть предложения — создайте pull request.

```python
--8<-- "examples/jetton/dex/dedust/swap_ton_to_jetton.py"
```

#### Обмен Jetton → TON

!!! note
    Перед использованием обязательно ознакомьтесь с официальной документацией [DeDust.io](https://docs.dedust.io/docs/introduction).
    Используйте с осторожностью и **всегда тестируйте сначала в тестовой сети**.
    Автор не несёт **никакой ответственности** за возможные потери средств.
    Нашли ошибку или есть предложения — создайте pull request.

```python
--8<-- "examples/jetton/dex/dedust/swap_jetton_to_ton.py"
```

#### Обмен Jetton → Jetton

!!! note
    Перед использованием обязательно ознакомьтесь с официальной документацией [DeDust.io](https://docs.dedust.io/docs/introduction).
    Используйте с осторожностью и **всегда тестируйте сначала в тестовой сети**.
    Автор не несёт **никакой ответственности** за возможные потери средств.
    Нашли ошибку или есть предложения — создайте pull request.

```python
--8<-- "examples/jetton/dex/dedust/swap_jetton_to_jetton.py"
```
