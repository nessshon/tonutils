Чтобы получить код и данные контракта, вы можете воспользоваться обозревателями TON, такими как [tonviewer.com](https://tonviewer.com), [tonscan.org](https://tonscan.org) и др., либо получить информацию программно с помощью метода `get_raw_account`.

---

### Через обозреватели TON

1. Перейдите на сайт [Tonviewer](https://tonviewer.com).
2. Введите адрес контракта в строку поиска.
3. Откройте вкладку **Code**.
4. В разделе **Bytecode** представлен код контракта.
5. В разделе **Raw data** представлены данные контракта.

---

### Через метод `get_raw_account`

```python
from tonutils.client import ToncenterV3Client


async def main() -> None:
    client = ToncenterV3Client()
    contract_address = "EQ..."
    account = await client.get_raw_account(contract_address)

    # Print contract code (hex-encoded BOC)
    print(account.code.to_boc().hex())

    # Print contract data (hex-encoded BOC)
    print(account.data.to_boc().hex())

    
if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

[Обзор полей RawAccount](get-contract-information.md/#rawaccount)
