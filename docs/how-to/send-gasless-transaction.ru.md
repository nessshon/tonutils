Этот пример демонстрирует, как выполнить **перевод Jetton без оплаты газа** (gasless).

!!! note
    Метод использует функцию gasless relayer, предоставляемую сервисом [tonapi.io](https://tonapi.io).
    Для использования необходимо получить API-ключ на [tonconsole.com](https://tonconsole.com).

---

### Предварительные требования

Установите зависимости:

```bash
pip install pytonapi
```

---

### Пример

```python
--8<-- "examples/wallet/send_gasless_transaction.py"
```
