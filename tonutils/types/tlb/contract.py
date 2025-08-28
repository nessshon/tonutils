import abc
import typing as t

from pytoniq_core import TlbScheme


class BaseContractData(TlbScheme, abc.ABC):

    def __init__(self, **kwargs: t.Any) -> None: ...
