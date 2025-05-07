---

### cell_hash

Calculates the representation hash of the given cell c and returns it as a 256-bit unsigned integer x. This function is handy for signing and verifying signatures of arbitrary entities structured as a tree of cells.

```python
from tonutils.utils import cell_hash
from pytoniq_core import begin_cell

def main() -> None:
    c = begin_cell().store_string("ness").end_cell()
    cell_hash_result = cell_hash(c)
    print(f"bytes: {cell_hash_result[0]}")
    print(f"int: {cell_hash_result[1]}")

if __name__ == "__main__":
    main()
```

---

### slice_hash

Computes the hash of the given slice s and returns it as a 256-bit unsigned integer x. The result is equivalent to creating a standard cell containing only the data and references from s and then computing its hash using cell_hash.

```python
from tonutils.utils import slice_hash
from pytoniq_core import begin_cell

def main() -> None:
    s = begin_cell().store_string("ness")
    slice_hash_result = slice_hash(s)
    print(f"bytes: {slice_hash_result[0]}")
    print(f"int: {slice_hash_result[1]}")

if __name__ == "__main__":
    main()
```

---

### string_hash

Calculates the SHA-256 hash of the data bits in the given slice s. A cell underflow exception is thrown if the bit length of s is not a multiple of eight. The hash is returned as a 256-bit unsigned integer x.

```python
from tonutils.utils import string_hash

def main() -> None:
    string_hash_result = string_hash("ness")
    print(f"bytes: {string_hash_result[0]}")
    print(f"int: {string_hash_result[1]}")

if __name__ == "__main__":
    main()
```
