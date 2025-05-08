This example shows how to retrieve full contract details, including balance, status, code, data, and last transaction metadata.

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

### `RawAccount` fields overview

- **balance** → integer (in nanoTON)  
  Current balance of the contract.

- **status** → string  
  Contract status, one of:
    - `active` → contract exists and is active
    - `nonexist` → contract does not exist
    - `frozen` → contract is frozen
    - `uninit` → contract exists but is not initialized

- **code** → `Cell` (optional)  
  The contract’s executable code (if present).

- **data** → `Cell` (optional)  
  The contract’s persistent data (if present).

- **last_transaction_lt** → integer (optional)  
  Logical time (LT) of the most recent transaction.

- **last_transaction_hash** → string (optional)  
  Hash of the most recent transaction.

- **state_init** → `StateInit` (optional)  
  Combined object representing the full contract state if both code and data are available.
