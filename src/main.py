# src/context7/main.py
import uvicorn

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from context7.exceptions import AppException
from context7.settings import settings
from context7.logger import pretty_logging, logger
from context7.api import router as mcp_router


fastapi_app = FastAPI(
    title="Context7",
    description="An assistant that helps answering software development related questions with context7.",
    version="0.1.0",
)

fastapi_app.include_router(mcp_router, prefix=settings.api_path)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp_server = FastApiMCP(
    fastapi_app,
    include_operations=[
        "get_default_prompt",
        "resolve_library_id",
        "get_library_docs",
        "resolve_multiple_library_ids",
        "get_multiple_library_docs",
    ],
)
mcp_server.mount_http()


@fastapi_app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "exception": exc, "request": request},
    )


@fastapi_app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error", "exception": exc, "request": request},
    )


def main():
    pretty_logging(fastapi_app, settings, mcp_server)

    if settings.cert_file is None or settings.key_file is None:
        logger.info("Use no tls.")
        ssl_certfile = None
        ssl_keyfile = None
    else:
        logger.info("Using tls.")
        ssl_certfile = settings.cert_file
        ssl_keyfile = settings.key_file

    uvicorn.run(
        fastapi_app,
        host=settings.app_host,
        port=settings.app_port,
        root_path=settings.app_root_path,
        log_config=None,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
    )


if __name__ == "__main__":
    main()
