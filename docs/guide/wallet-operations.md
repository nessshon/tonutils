This section provides a complete guide to managing wallets using the `tonutils` library.
It covers key operations such as:

* Creating and deploying wallets
* Importing wallets from mnemonic or private key
* Sending transactions (TON, NFTs, Jettons)
* Performing batch transfers
* Executing Jetton swaps (via **STON.fi** and **DeDus.io**)

---

### Supported Wallet

The library supports multiple wallet versions and types:

* **Standard wallets**:
  `WalletV2R1`, `WalletV2R2`, `WalletV3R1`, `WalletV3R2`, `WalletV4R1`, `WalletV4R2`, `WalletV5R1`
* **Highload wallets** (for services and exchanges):
  `HighloadWalletV2`, `HighloadWalletV3`
* **Preprocessed wallets** (for economical batch operations):
  `PreprocessedWalletV2`, `PreprocessedWalletV2R1`

---

### Recommendations

* For **general use**, it’s recommended to work with wallet versions **v3r2 to v5r1**, preferably **v5r1** for full feature support.
* For **service and exchange integrations**, use **HighloadWalletV3**.
* For **large-scale batch transfers** where gas optimization is critical, use **PreprocessedWallet** types.

---

## Create Wallet

To create a new wallet, use the `.create()` method provided by the wallet class you select.
This generates a wallet instance along with its **public key**, **private key**, and **mnemonic** phrase.

```python
--8<-- "examples/wallet/create_wallet.py"
```

## Import Wallet

You can import a wallet either from a **mnemonic** phrase or directly from a **private key**.

---

### From Mnemonic

```python
--8<-- "examples/wallet/import_from_mnemonic.py"
```

---

### From Private Key

```python
--8<-- "examples/wallet/import_from_private_key.py"
```

---

## Deploy Wallet

To deploy a wallet, reconstruct it from a mnemonic and call the `.deploy()` method.
This will publish the wallet contract on-chain.

```python
--8<-- "examples/wallet/deploy_wallet.py"
```

---

## Transfers

### Send TON

```python
--8<-- "examples/wallet/common/transfer_ton.py"
```

### Send NFT

```python
--8<-- "examples/wallet/common/transfer_nft.py"
```

### Send Jetton

```python
--8<-- "examples/wallet/common/transfer_jetton.py"
```

---

## Batch Transfers

### Batch Send TON

```python
--8<-- "examples/wallet/common/batch_transfer_ton.py"
```

### Batch Send NFT

```python
--8<-- "examples/wallet/common/batch_transfer_nft.py"
```

### Batch Send Jetton

```python
--8<-- "examples/wallet/common/batch_transfer_jetton.py"
```

---

## Jetton Swaps

### Using STON.fi

#### Swap TON → Jetton

```python
--8<-- "examples/wallet/common/dex/stonfi/swap_ton_to_jetton.py"
```

#### Swap Jetton → TON

```python
--8<-- "examples/wallet/common/dex/stonfi/swap_jetton_to_ton.py"
```

#### Swap Jetton → Jetton

```python
--8<-- "examples/wallet/common/dex/stonfi/swap_jetton_to_jetton.py"
```

#### Batch Swap TON → Jetton

```python
--8<-- "examples/wallet/common/dex/stonfi/batch_swap_ton_to_jetton.py"
```

#### Batch Swap Jetton → TON

```python
--8<-- "examples/wallet/common/dex/stonfi/batch_swap_jetton_to_ton.py"
```

#### Batch Swap Jetton → Jetton

```python
--8<-- "examples/wallet/common/dex/stonfi/batch_swap_jetton_to_jetton.py"
```

### Using DeDus.io

#### Swap TON → Jetton

```python
--8<-- "examples/wallet/common/dex/dedust/swap_ton_to_jetton.py"
```

#### Swap Jetton → TON

```python
--8<-- "examples/wallet/common/dex/dedust/swap_jetton_to_ton.py"
```

#### Swap Jetton → Jetton

```python
--8<-- "examples/wallet/common/dex/dedust/swap_jetton_to_jetton.py"
```

#### Batch Swap TON → Jetton

```python
--8<-- "examples/wallet/common/dex/dedust/batch_swap_ton_to_jetton.py"
```

#### Batch Swap Jetton → TON

```python
--8<-- "examples/wallet/common/dex/dedust/batch_swap_jetton_to_ton.py"
```

#### Batch Swap Jetton → Jetton

```python
--8<-- "examples/wallet/common/dex/dedust/batch_swap_jetton_to_jetton.py"
```
