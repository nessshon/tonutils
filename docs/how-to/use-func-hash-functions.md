### cell_hash

Calculates the representation hash of the given cell `c` and returns it as a 256-bit unsigned integer `x`. This function is handy for signing and verifying signatures of arbitrary entities structured as a tree of cells.

```python
from tonutils.utils import cell_hash
from pytoniq_core import begin_cell


def main() -> None:
    c = begin_cell().store_string("ness").end_cell()
    x = cell_hash(c)
    print(x)


if __name__ == "__main__":
    main()
```

---

### slice_hash

Computes the hash of the given slice `s` and returns it as a 256-bit unsigned integer `x`. The result is equivalent to creating a standard cell containing only the data and references from `s` and then computing its hash using `cell_hash`.

```python
from tonutils.utils import slice_hash
from pytoniq_core import begin_cell


def main() -> None:
    s = begin_cell().store_string("ness")
    x = slice_hash(s)
    print(x)


if __name__ == "__main__":
    main()
```

---

### string_hash

Calculates the SHA-256 hash of the data bits in the given slice `s`. A cell underflow exception is thrown if the bit length of `s` is not a multiple of eight. The hash is returned as a 256-bit unsigned integer `x`.

```python
from tonutils.utils import string_hash


def main() -> None:
    s = "ness"
    x = string_hash(s)
    print(x)


if __name__ == "__main__":
    main()
```
