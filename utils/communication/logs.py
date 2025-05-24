from models import OperationResult


def operation_failed(
        email: str,
        email_password: str = None,
        account_password: str = None,
        data: str | dict = None,
) -> OperationResult:
    return OperationResult(
        email=email,
        email_password=email_password,
        account_password=account_password,
        data=data,
        success=False,
    )


def operation_success(
        email: str,
        email_password: str = None,
        account_password: str = None,
        data: str | dict = None,
) -> OperationResult:
    return OperationResult(
        email=email,
        email_password=email_password,
        account_password=account_password,
        data=data,
        success=True,
    )
