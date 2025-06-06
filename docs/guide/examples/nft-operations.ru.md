Этот раздел предоставляет полное руководство по работе с NFT-коллекциями с использованием библиотеки `tonutils`.
Описаны коллекции типов **Standard**, **Soulbound**, **Editable** и **Editable Onchain**, включая развёртывание, выпуск, пакетные операции, редактирование и административные действия.

---

### Standard коллекция

#### Развёртывание коллекции

```python
--8<-- "examples/nft/standard/deploy_collection.py"
```

#### Выпуск NFT

```python
--8<-- "examples/nft/standard/mint_nft.py"
```

#### Пакетный выпуск NFT

```python
--8<-- "examples/nft/standard/batch_mint_nft.py"
```

---

### Soulbound коллекция

#### Развёртывание коллекции

```python
--8<-- "examples/nft/soulbound/deploy_collection.py"
```

#### Выпуск NFT

```python
--8<-- "examples/nft/soulbound/mint_nft.py"
```

#### Пакетный выпуск NFT

```python
--8<-- "examples/nft/soulbound/batch_mint_nft.py"
```

#### Отзыв NFT

```python
--8<-- "examples/nft/soulbound/revoke_nft.py"
```

#### Уничтожить NFT

```python
--8<-- "examples/nft/soulbound/destroy_nft.py"
```

---

### Editable коллекция

#### Развёртывание коллекции

```python
--8<-- "examples/nft/editable/deploy_collection.py"
```

#### Выпуск NFT

```python
--8<-- "examples/nft/editable/mint_nft.py"
```

#### Пакетный выпуск NFT

```python
--8<-- "examples/nft/editable/batch_mint_nft.py"
```

#### Редактирование контента NFT

```python
--8<-- "examples/nft/editable/edit_nft_content.py"
```

#### Передача прав редактирования NFT

```python
--8<-- "examples/nft/editable/change_nft_editorship.py"
```

#### Редактирование контента коллекции

```python
--8<-- "examples/nft/editable/edit_collection_content.py"
```

#### Передача прав на коллекцию

```python
--8<-- "examples/nft/editable/change_collection_owner.py"
```

---

### Editable-onchain коллекция

#### Развёртывание коллекции

```python
--8<-- "examples/nft/deploy_onchain_collection.py"
```

#### Выпуск NFT

```python
--8<-- "examples/nft/mint_onchain_nft.py"
```

#### Возврат баланса коллекции

```python
--8<-- "examples/nft/return_collection_balance.py"
```

### Продажа NFT на Getgems.io

#### Выставить NFT на продажу

```python
--8<-- "examples/nft/marketplace/getgems/put_on_sale.py"
```

#### Изменить цену NFT

```python
--8<-- "examples/nft/marketplace/getgems/change_price.py"
```

#### Снять NFT с продажи

```python
--8<-- "examples/nft/marketplace/getgems/cancel_sale.py"
```
