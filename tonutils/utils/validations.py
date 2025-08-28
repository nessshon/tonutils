import typing as t

from pytoniq_core.crypto.keys import words

VALID_MNEMONIC_LENGTHS: t.Final[t.Tuple[int, ...]] = (12, 18, 24)


def validate_mnemonic(mnemonic: t.Union[str, t.List[str]]) -> None:
    if isinstance(mnemonic, str):
        mnemonic_words = mnemonic.strip().lower().split()
    else:
        mnemonic_words = [w.strip().lower() for w in mnemonic]

    if len(mnemonic_words) not in VALID_MNEMONIC_LENGTHS:
        raise ValueError(
            f"Invalid mnemonic length: {len(mnemonic_words)}. "
            f"Expected one of {sorted(VALID_MNEMONIC_LENGTHS)}."
        )

    invalid = [(i + 1, w) for i, w in enumerate(mnemonic_words) if w not in words]
    if invalid:
        formatted = ", ".join(f"{idx}. {word}" for idx, word in invalid)
        raise ValueError(f"Invalid mnemonic word(s): {formatted}")
