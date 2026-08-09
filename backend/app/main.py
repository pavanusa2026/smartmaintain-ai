import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.core.security import decode_token
from app.core.security_middleware import SecurityHeadersMiddleware
from app.services.seed_service import seed_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connected_clients: list[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    seed_database(settings)
    logger.info("SmartMaintain AI started")
    yield
    logger.info("SmartMaintain AI shutting down")


def _safe_static_path(static_dir: Path, full_path: str) -> Path | None:
    """Resolve a path and ensure it stays within static_dir."""
    if not full_path or full_path in {".", ".."}:
        return None
    try:
        resolved = (static_dir / full_path).resolve()
        static_resolved = static_dir.resolve()
        resolved.relative_to(static_resolved)
    except (ValueError, OSError):
        return None
    return resolved if resolved.is_file() else None


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="AI Predictive Maintenance and Quality Monitoring System",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    app.include_router(api_router, prefix="/api")
    register_error_handlers(app)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "smart-maintain-ai"}

    @app.get("/ready")
    async def readiness_check():
        if settings.debug:
            return {
                "status": "ready",
                "storage": settings.storage_backend,
                "model": "local" if settings.use_local_model else "sagemaker",
            }
        return {"status": "ready"}

    @app.websocket("/ws/live")
    async def websocket_live(websocket: WebSocket):
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        try:
            decode_token(token)
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        connected_clients.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            if websocket in connected_clients:
                connected_clients.remove(websocket)

    static_dir = Path(settings.static_dir)
    if static_dir.exists():
        app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api/"):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            file_path = _safe_static_path(static_dir, full_path)
            if file_path:
                return FileResponse(file_path)
            index = static_dir / "index.html"
            if index.exists():
                return FileResponse(index)
            return JSONResponse(
                status_code=503,
                content={"message": "Frontend not built. Run npm run build in frontend/"},
            )

    return app


app = create_app()
