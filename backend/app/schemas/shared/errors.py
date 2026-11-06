from app.schemas.shared.base import Output


class ErrorDetail(Output):
    code: str
    message: str


class ErrorOut(Output):
    error: ErrorDetail
