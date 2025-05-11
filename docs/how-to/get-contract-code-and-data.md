To retrieve the code and data of a contract, you can use TON explorers such as [tonviewer.com](https://tonviewer.com), [tonscan.org](https://tonscan.org), and others, or use the `get_raw_account` method programmatically.

---

### Using TON explorers

1. Open [Tonviewer](https://tonviewer.com).
2. Enter the contract address into the search field.
3. Navigate to the **Code** tab.
4. The **Bytecode** section contains the contract code.
5. The **Raw data** section contains the contract data.

---

### Using `get_raw_account` method

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

[See RawAccount fields overview](get-contract-information.md/#_2)
