# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import time

from config import settings, get_logger
from app.api.router import api_router

# Get logger
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    logger.info(f"Starting {settings.app_name} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API prefix: {settings.api_prefix}")
    yield
    logger.info(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "Job Market Intelligence Team",
            "email": "support@jobmarketintelligence.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "Health",
                "description": "Health check and monitoring endpoints"
            },
            {
                "name": "Jobs",
                "description": "Job search, filtering, and retrieval operations"
            },
            {
                "name": "Analytics",
                "description": "Analytics and insights about the job market"
            },
        ],
    )

    # Request logging middleware (clean, no emojis)
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log HTTP requests with timing."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Clean request logging - no emojis
        status_indicator = "OK" if response.status_code < 400 else "ERR" if response.status_code < 500 else "ERR"
        logger.info(
            f"{request.method} {request.url.path} | "
            f"status={response.status_code} | "
            f"duration={process_time:.3f}s"
        )
        return response

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers with clean messages
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(f"Validation error on {request.url.path}: {len(exc.errors())} errors")
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "status_code": 422,
                "path": request.url.path,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError):
        """Handle database errors."""
        logger.error(f"Database error on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "A database error occurred. Please try again later.",
                "status_code": 500,
                "path": request.url.path,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    @app.exception_handler(Exception)
    async def handle_general_error(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Please try again later.",
                "status_code": 500,
                "path": request.url.path,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    # Routes
    app.include_router(api_router)

    return app


app = create_app()


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_prefix}/health",
    }