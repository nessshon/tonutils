### cell_hash

Вычисляет хеш представления заданной ячейки `c` и возвращает его в виде 256-битного без знакового целого числа `x`. Эта функция полезна для подписания и проверки подписей произвольных сущностей, структурированных в виде дерева ячеек.

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

Вычисляет хеш заданного среза `s` и возвращает его в виде 256-битного без знакового целого числа `x`. Результат эквивалентен созданию стандартной ячейки, содержащей только данные и ссылки из `s`, с последующим вычислением её хеша с помощью `cell_hash`.

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

Вычисляет SHA-256 хеш битов данных в заданном срезе `s`. Если длина `s` в битах не кратна восьми, возникает исключение cell underflow. Хеш возвращается в виде 256-битного беззнакового целого числа `x`.

```python
from tonutils.utils import string_hash


def main() -> None:
    s = "ness"
    x = string_hash(s)
    print(x)


if __name__ == "__main__":
    main()
```
