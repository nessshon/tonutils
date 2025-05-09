This section provides a complete guide to working with Jettons using the `tonutils` library.
It covers operations for both **Stablecoin Jettons** and **Standard Jettons**, including deployment, minting, burning, administration, and swaps through decentralized exchanges like **STON.fi** and **DeDust.io**.

---

## Stablecoin Jetton

### Deploy Jetton Master

```python
--8<-- "examples/jetton/stablecoin/deploy_master.py"
```

### Upgrade Contract

```python
--8<-- "examples/jetton/stablecoin/upgrade_contract.py"
```

### Mint Jetton

```python
--8<-- "examples/jetton/stablecoin/mint_jetton.py"
```

### Burn Jetton

```python
--8<-- "examples/jetton/stablecoin/burn_jetton.py"
```

### Change Admin

```python
--8<-- "examples/jetton/stablecoin/change_admin.py"
```

### Drop Admin

```python
--8<-- "examples/jetton/stablecoin/drop_admin.py"
```

### Change Content

```python
--8<-- "examples/jetton/stablecoin/change_content.py"
```

---

## Standard Jetton

### Deploy Jetton Master Onchain

```python
--8<-- "examples/jetton/standard/deploy_master_onchain.py"
```

### Deploy Jetton Master Offchain

```python
--8<-- "examples/jetton/standard/deploy_master_offchain.py"
```

### Mint Jetton

```python
--8<-- "examples/jetton/standard/mint_jetton.py"
```

### Burn Jetton

```python
--8<-- "examples/jetton/standard/burn_jetton.py"
```

### Change Admin

```python
--8<-- "examples/jetton/standard/change_admin.py"
```

### Change Content

```python
--8<-- "examples/jetton/standard/change_content.py"
```

---

## Swap Jettons

### Using STON.fi

#### Swap TON → Jetton

!!! note
    Before using these instructions, **please consult the official documentation** of [STON.fi](https://docs.ston.fi/).
    Use with caution and **always test carefully on a testnet** first.
    I take **no responsibility** for any lost funds.
    If you find errors or have suggestions for improvement, feel free to **open a pull request** — let’s make this better together.

```python
--8<-- "examples/jetton/dex/stonfi/swap_ton_to_jetton.py"
```

#### Swap Jetton → TON

!!! note
    Before using these instructions, **please consult the official documentation** of [STON.fi](https://docs.ston.fi/).
    Use with caution and **always test carefully on a testnet** first.
    I take **no responsibility** for any lost funds.
    If you find errors or have suggestions for improvement, feel free to **open a pull request** — let’s make this better together.

```python
--8<-- "examples/jetton/dex/stonfi/swap_jetton_to_ton.py"
```

#### Swap Jetton → Jetton

!!! note
    Before using these instructions, **please consult the official documentation** of [STON.fi](https://docs.ston.fi/).
    Use with caution and **always test carefully on a testnet** first.
    I take **no responsibility** for any lost funds.
    If you find errors or have suggestions for improvement, feel free to **open a pull request** — let’s make this better together.

```python
--8<-- "examples/jetton/dex/stonfi/swap_jetton_to_jetton.py"
```

### Using DeDust.io

#### Swap TON → Jetton

!!! note
    Before using these instructions, **please consult the official documentation** of [DeDust.io](https://docs.dedust.io/docs/introduction).
    Use with caution and **always test carefully on a testnet** first.
    I take **no responsibility** for any lost funds.
    If you find errors or have suggestions for improvement, feel free to **open a pull request** — let’s make this better together.

```python
--8<-- "examples/jetton/dex/dedust/swap_ton_to_jetton.py"
```

#### Swap Jetton → TON

!!! note
    Before using these instructions, **please consult the official documentation** of [DeDust.io](https://docs.dedust.io/docs/introduction).
    Use with caution and **always test carefully on a testnet** first.
    I take **no responsibility** for any lost funds.
    If you find errors or have suggestions for improvement, feel free to **open a pull request** — let’s make this better together.

```python
--8<-- "examples/jetton/dex/dedust/swap_jetton_to_ton.py"
```

#### Swap Jetton → Jetton

!!! note
    Before using these instructions, **please consult the official documentation** of [DeDust.io](https://docs.dedust.io/docs/introduction).
    Use with caution and **always test carefully on a testnet** first.
    I take **no responsibility** for any lost funds.
    If you find errors or have suggestions for improvement, feel free to **open a pull request** — let’s make this better together.

```python
--8<-- "examples/jetton/dex/dedust/swap_jetton_to_jetton.py"
```
