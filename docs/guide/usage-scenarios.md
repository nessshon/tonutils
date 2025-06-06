This section provides practical examples of working with the `tonutils` library. You will learn how to create and import wallets, send transactions, retrieve contract data, and call methods on the TON network.

---

## Working with Wallets

### Creating a Wallet

```python
from tonutils.wallet import WalletV4R2
from tonutils.client import ToncenterV3Client

client = ToncenterV3Client(is_testnet=True, rps=1)
wallet, public_key, private_key, mnemonic = WalletV4R2.create(client)
```

**Result:**

- `wallet`: an instance of `WalletV4R2`, ready to use
- `public_key`: byte representation of the public key (`bytes`)
- `private_key`: byte representation of the private key (`bytes`)
- `mnemonic`: list of 24 words (`List[str]`)

---

### Importing a Wallet

```python
wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)
```

**Parameter:**

- `MNEMONIC` — can be provided in one of two formats:
    - a string of 12/24 space-separated words;
    - a list of 12/24 words.

---

## Sending Transactions

### Single Transaction

```python
tx_hash = await wallet.transfer(
    destination="nessshon.t.me",
    amount=1,
    body="Hello from tonutils!",
)
```

**Parameters:**

- `destination`: the recipient — can be:
    - a string with the address;
    - an `Address` object;
    - a `.ton` or `.t.me` domain name;
- `amount`: amount in TON (not in nanotons);
- `body`: comment as a string or custom data as a `Cell`.

**Result:**

- Normalized transaction hash (`str`)

---

### Batch Transfer

Allows sending multiple transfers in a single transaction:

```python
from tonutils.wallet.messages import TransferMessage

tx_hash = await wallet.batch_transfer_messages([
    TransferMessage(destination="UQ...", amount=0.01, body="Hello from tonutils!"),
    TransferMessage(destination="UQ...", amount=0.02, body="Hello from tonutils!"),
])
```

**Result:**

- Normalized transaction hash (`str`)

---

### Send Mode

The `send_mode` parameter controls transaction behavior — for example, it can send the entire balance (`128`).

```python
await wallet.transfer(
    destination="UQ...",
    amount=0,
    send_mode=128,
)
```

!!! note
    For more details on available send modes, see the [official TON documentation](https://docs.ton.org/v3/documentation/smart-contracts/message-management/message-modes-cookbook).

---

## Contract Information

### Contract Balance

```python
balance = await client.get_account_balance("UQ...")
```

**Result:**

An integer (`int`) representing the contract balance in nanotons.

---

### Contract Data

```python
contract_data = await client.get_raw_account("UQ...")
```

**Result:**

An object containing contract information with the following fields:

- `balance`: current contract balance in nanotons (`int`);
- `status`: account state: `active`, `nonexist`, `frozen`, `uninit`;
- `code`: contract code (`Optional[Cell]`);
- `data`: contract data (`Optional[Cell]`);
- `last_transaction_lt`: logical time of the last transaction (`Optional[int]`);
- `last_transaction_hash`: hash of the last transaction (`Optional[str]`);
- `state_init`: `StateInit` object if `code` and `data` are present.

---

## Calling a Contract Method

The `run_get_method` function allows invoking a contract's `get-method`.

```python
result = await client.run_get_method(
    address="UQ...",
    method_name="get_my_data",
    stack=[0]
)
```

**Parameters:**

- `address`: contract address as a string;
- `method_name`: name of the method to call (`str`);
- `stack`: list of arguments (supported types: `int`, `Cell`, `Slice`).

**Result:**

A list of values returned from the method's execution stack.
