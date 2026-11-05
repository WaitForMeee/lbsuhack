from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routes.auth.router import router as auth_router
from app.routes.categories.router import router as categories_router
from app.routes.events.router import router as events_router
from app.routes.organizations.router import router as organizations_router
from app.routes.partnerships.router import router as partnerships_router
from app.routes.profiles.router import router as profiles_router
from app.routes.registrations.router import router as registrations_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def check_trusted_origin(request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin is not None and origin.rstrip("/") not in settings.allowed_origins:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Недоверенный источник запроса"},
                )
        return await call_next(request)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(categories_router, prefix=settings.api_prefix)
    app.include_router(profiles_router, prefix=settings.api_prefix)
    app.include_router(events_router, prefix=settings.api_prefix)
    app.include_router(registrations_router, prefix=settings.api_prefix)
    app.include_router(organizations_router, prefix=settings.api_prefix)
    app.include_router(partnerships_router, prefix=settings.api_prefix)
    configure_frontend(app, settings.frontend_dist_path)
    return app


def configure_frontend(app: FastAPI, configured_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    dist_path = configured_path if configured_path.is_absolute() else (backend_root / configured_path).resolve()
    index_file = dist_path / "index.html"
    assets_path = dist_path / "assets"

    if assets_path.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_path), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/") or "." in Path(full_path).name or not index_file.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return FileResponse(index_file)


app = create_app()
