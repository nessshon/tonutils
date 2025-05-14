There are several ways to obtain the address of an NFT Item.

---

### Standard collections

#### Using get-method

```python
from tonutils.client import ToncenterV3Client
from tonutils.nft import Collection


async def main() -> None:
    client = ToncenterV3Client()
    nft_index = 1
    collection_address = "EQ..."

    nft_address = await Collection.get_nft_address_by_index(
        client,
        nft_index,
        collection_address,
    )
    print(nft_address.to_str())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

#### Calculating locally

!!! note
    Prepare the NFT Item contract code by following the instructions in [Get Contract code and data](get-contract-code-and-data.md).

```python
from tonutils.nft import Collection


def main() -> None:
    nft_index = 1
    nft_item_code = "..."
    collection_address = "EQ..."

    nft_address = Collection.calculate_nft_item_address(
        nft_index,
        nft_item_code,
        collection_address,
    )
    print(nft_address.to_str())


if __name__ == "__main__":
    main()
```

---

### TON DNS Domains collection

!!! note
    The index is computed as `slice_hash(name)`. See [Use FunC hash functions](use-func-hash-functions.md/#slice_hash) for details.

#### Using get-method

```python
from pytoniq_core import begin_cell
from tonutils.client import ToncenterV3Client
from tonutils.nft import Collection
from tonutils.utils import slice_hash


async def main() -> None:
    client = ToncenterV3Client()
    domain_name = "temp"
    domain_index = slice_hash(begin_cell().store_string(domain_name))
    collection_address = "EQ..."

    nft_address = await Collection.get_nft_address_by_index(
        client,
        domain_index,
        collection_address,
    )
    print(nft_address.to_str())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

#### Calculating locally

!!! note
    Prepare the NFT Item contract code by following the instructions in [Get Contract code and data](get-contract-code-and-data.md).

```python
from pytoniq_core import begin_cell
from tonutils.nft import Collection
from tonutils.utils import slice_hash


def main() -> None:
    domain_name = "temp"
    domain_index = slice_hash(begin_cell().store_string(domain_name))
    nft_item_code = "..."
    collection_address = "EQ..."

    nft_address = Collection.calculate_nft_item_address(
        domain_index,
        nft_item_code,
        collection_address,
        index_len=256,
    )
    print(nft_address.to_str())


if __name__ == "__main__":
    main()
```

---

### Telegram Gifts / Anonymous Telegram Numbers

!!! note
    The index is computed as `string_hash(telemint_token_name)`. See [Use FunC hash functions](use-func-hash-functions.md/#string_hash) for details.

#### Using get-method

```python
from tonutils.client import ToncenterV3Client
from tonutils.nft import Collection
from tonutils.utils import string_hash


async def main() -> None:
    client = ToncenterV3Client()
    telemint_token_name = "8888888"
    token_index = string_hash(telemint_token_name)
    collection_address = "EQ..."

    nft_address = await Collection.get_nft_address_by_index(
        client,
        token_index,
        collection_address,
    )
    print(nft_address.to_str())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

#### Calculating locally

!!! note
    Prepare the NFT Item contract code by following the instructions in [Get Contract code and data](get-contract-code-and-data.md).

```python
from tonutils.nft import Collection
from tonutils.utils import string_hash


def main() -> None:
    telemint_token_name = "8888888"
    token_index = string_hash(telemint_token_name)
    nft_item_code = "..."
    collection_address = "EQ..."

    nft_address = Collection.calculate_nft_item_address(
        token_index,
        nft_item_code,
        collection_address,
        index_len=256,
        is_telemint_token=True,
    )
    print(nft_address.to_str())


if __name__ == "__main__":
    main()
```
