"""Safe, content-free error codes suitable for traces."""


class RuntimeFault(Exception):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.retryable = retryable


class ConflictError(RuntimeFault):
    def __init__(self) -> None:
        super().__init__("revision_conflict")
