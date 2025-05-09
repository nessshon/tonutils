This guide shows how to generate **multiple wallet addresses** from a single mnemonic by changing the `subwallet_id`.
Each `subwallet_id` produces a unique address under the same seed phrase.

---

### Example

```python
from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Subwallet ID
WALLET_ID = 0


def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC, WALLET_ID)

    print(f"Address: {wallet.address.to_str()}")


if __name__ == "__main__":
    main()
```

---

### Explanation

* **`subwallet_id`** → a 32-bit integer used to derive distinct wallet addresses from the same mnemonic.
* **Use cases**:

    * Splitting funds across logical accounts.
    * Managing separate balances.
    * Creating derived wallets for contract operations.

---

### Important Notes

* `subwallet_id` (or `wallet_id`) **is not supported** in:

    * `WalletV2*`
    * `PreprocessedWallet*`

* **Default `wallet_id` values**:

    * All wallet types except `WalletV5R1` → `698983191`
    * `WalletV5R1`:

        | global_id | workchain | wallet_version | subwallet_number | wallet_id  |
        |-----------|-----------|----------------|------------------|------------|
        | -239      | 0         | 0              | 0                | 2147483409 |
        | -239      | -1        | 0              | 0                | 8388369    |
        | -3        | 0         | 0              | 0                | 2147483645 |
        | -3        | -1        | 0              | 0                | 8388605    |
