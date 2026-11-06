from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import get_settings
from app.routes import (
    auth,
    events,
    moderation,
    notifications,
    organizations,
    parents,
    partnerships,
    reference,
    registrations,
    students,
)
from app.schemas.shared.errors import ErrorOut


def create_app():
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        description="TalentHub API for an independently deployed frontend. Bearer sessions expire in eight hours.",
        responses={code: {"model": ErrorOut} for code in (401, 403, 404, 409, 422)},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        detail = (
            exc.detail
            if isinstance(exc.detail, dict)
            else dict(
                code={
                    401: "authentication_required",
                    403: "forbidden",
                    404: "not_found",
                }.get(exc.status_code, "http_error"),
                message=str(exc.detail),
            )
        )
        headers = dict(exc.headers or {})
        if exc.status_code == 401:
            headers["WWW-Authenticate"] = "Bearer"
        return JSONResponse(
            status_code=exc.status_code, content={"error": detail}, headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        message = "; ".join(
            ".".join(str(p) for p in e["loc"]) + ": " + e["msg"] for e in exc.errors()
        )
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": message}},
        )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for module in (
        auth,
        reference,
        students,
        parents,
        organizations,
        events,
        registrations,
        notifications,
        partnerships,
        moderation,
    ):
        app.include_router(module.router, prefix=settings.api_prefix)
    return app


app = create_app()
