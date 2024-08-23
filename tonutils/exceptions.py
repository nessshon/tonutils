class TonutilsException(Exception):
    pass


class UnknownClientError(TonutilsException):
    """
    Exception raised when an unknown client is provided.

    This exception informs the user that an unknown client was provided
    and provides guidance on how to fix it.
    """

    def __init__(self, input_client: str) -> None:
        super().__init__(
            f"Unknown client: {input_client}! "
            f"Please, specify one of: TonapiClient, ToncenterClient, LiteClient."
        )


class PytoniqDependencyError(TonutilsException):
    """
    Exception raised when pytoniq dependency is missing.

    This exception informs the user that the pytoniq library is required
    and provides guidance on how to install it.
    """

    def __init__(self) -> None:
        super().__init__(
            "The 'pytoniq' library is required to use LiteClient functionality. "
            "Please install it with 'pip install tonutils[pytoniq]'."
        )
