class PytoniqToolsException(Exception):
    pass


class UnknownClientError(PytoniqToolsException):

    def __init__(self, input_client: str) -> None:
        super().__init__(
            f"Unknown client: {input_client}! "
            f"Please, specify one of: TonapiClient, ToncenterClient, LiteClient."
        )
