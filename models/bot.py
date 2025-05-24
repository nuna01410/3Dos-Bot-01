from typing import Literal, TypedDict


ModuleType = Literal["register", "stats", "accounts", "verify", "login"]


class OperationResult(TypedDict):
    email: str
    email_password: str | None
    account_password: str | None
    data: str | dict | None
    success: bool
