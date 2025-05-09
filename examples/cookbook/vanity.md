## Introduction

This guide explains how to create **vanity addresses** on the TON blockchain — contracts or wallets with custom patterns (for example, specific starting or ending characters) that make the address visually distinctive. 
Vanity addresses are often used for branding, better recognizability, or aesthetic purposes.

---

## Vanity Contract Address

To create a **vanity contract address** (for example, for a Jetton Master contract), follow these steps.

### Clone the Repository

```bash
git clone https://github.com/ton-community/vanity-contract
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Generator

```bash
python src/generator/run.py --end {suffix} -w -0 --case-sensitive {owner_address}
```

- Replace `{suffix}` with the desired ending for the generated address.
- Replace `{owner_address}` with the wallet address from which the deployment will be made.

**Example:**

```bash
python src/generator/run.py --end NESS -w -0 --case-sensitive UQCZq3_Vd21-4y4m7Wc-ej9NFOhh_qvdfAkAYAOHoQ__Ness
```

If a match is found, you will see a message like:

```
Found: EQC7PA9iWnUVWv001Drj3vTu-pmAkTc30OarHy5iDJ1uNESS salt: 7c9398f0999a96fe5480b5d573817255d53377a000be18d0fb47d090a5606dfe
```

### Deploy the Contract

Copy the `salt` value and use it in the `SALT` constant in the deployment script:

```python
--8<-- "examples/vanity/deploy_contract.py"
```

---

## Vanity Wallet Address

To create a **vanity wallet address** using GPU acceleration, follow these steps.

### Check Requirements

NVIDIA GPU (driver version 555.* or later).

### Download Binary

Download the `gpu-generator-linux` binary from
the [latest release](https://github.com/ton-offline-storage/address-generator/releases).

### Run the Generator

To start the generator with interactive input:

```bash
./gpu-generator-linux
```

To run the generator with predefined constraints directly from the command line:

```bash
./gpu-generator-linux -q "start[*][T][O][N] | end[1][2][3]"
```

Follow the on-screen instructions to monitor progress and view results.

After a successful match, the tool will display the **mnemonic phrase** and the **wallet ID** for use with a `WalletV3R2` wallet.

**Constraints Syntax**

* **Allowed characters**: `A-Z`, `a-z`, `0-9`, `_`, `-`
* **Start constraint** (after `UQ` prefix, third character):

  Example → `start[A][P][P][L][E]` or `start[*][T][O][N]`

* **End constraint**:

  Example → `end[T][O][N]` or `end[Tt][Oo][Nn]`

* **Combined constraints**:

  Example → `start[*][T][O][N] & end[T][O][N]`

* **Multiple variants (OR)**:

  Example → `start[*][T][O][N] & end[T][O][N] | start[D][D][D] | end[0][0][0]`

**Performance Reference**

| Hardware              | 5 chars | 6 chars  | 7 chars   | 8 chars   |
|-----------------------|---------|----------|-----------|-----------|
| Intel i5-8350U        | 4 min   | 4 h 40 m | 12.5 days | > 2 years |
| AMD Ryzen 5 3600      | 26 sec  | 30 min   | 31.5 h    | 84 days   |
| NVIDIA GTX 1650 SUPER | 2 sec   | 2 min    | 2 h       | 5.5 days  |
| NVIDIA RTX 4090       | <1 sec  | 13 sec   | 13.5 min  | 14.5 h    |

### Use the Generated Wallet

After obtaining the mnemonic and wallet ID, use the following code:

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

## Conclusion
-------------

Vanity addresses are a cosmetic feature that can make your TON wallet or contract stand out. 
While they offer no functional advantage, they can be useful for branding, marketing, or personal aesthetics.

## See also
-----------

- [Vanity Contract Generator](https://github.com/ton-community/vanity-contract)
- [Vanity Wallet Generator](https://github.com/ton-offline-storage/address-generator)

