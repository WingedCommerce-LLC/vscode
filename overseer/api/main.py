"""
Overseer API - Main FastAPI Application
AI-Enabled Director Platform for Development Teams
"""

import time
import traceback
from datetime import datetime
from typing import Dict, Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load .env file from the project root
load_dotenv()

# Import configuration and logging
from config.settings import get_settings
from api.logging_config import setup_logging, set_correlation_id, clear_correlation_id, get_logger

# Import routers
from api.auth import router as auth_router
from api.health import router as health_router

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = get_logger(__name__)

# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="Overseer API",
    description="AI-Enabled Director Platform for Development Teams",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    debug=settings.DEBUG
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request correlation and timing middleware
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """
    Middleware to add request correlation ID, timing, and logging.
    """
    start_time = time.time()

    # Set correlation ID for request tracking
    correlation_id = request.headers.get("X-Correlation-ID") or set_correlation_id()

    # Log request start
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add headers to response
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-Timestamp"] = datetime.utcnow().isoformat()

        # Log request completion
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time

        # Log request error
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "process_time_ms": round(process_time * 1000, 2),
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
        )

        # Re-raise the exception to be handled by exception handlers
        raise

    finally:
        # Clear correlation ID after request
        clear_correlation_id()


# Enhanced exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions with structured error responses.
    """
    error_response = {
        "error": {
            "type": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code,
        },
        "request": {
            "method": request.method,
            "path": request.url.path,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed field information.
    """
    error_response = {
        "error": {
            "type": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
        "request": {
            "method": request.method,
            "path": request.url.path,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    logger.warning(
        f"Validation Error: {request.method} {request.url.path}",
        extra={
            "validation_errors": exc.errors(),
            "path": request.url.path,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with proper logging and user-friendly responses.
    """
    error_id = set_correlation_id()

    error_response = {
        "error": {
            "type": "InternalServerError",
            "message": "An unexpected error occurred",
            "error_id": error_id,
        },
        "request": {
            "method": request.method,
            "path": request.url.path,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Log the full exception details
    logger.error(
        f"Unhandled Exception: {request.method} {request.url.path} - {str(exc)}",
        extra={
            "error_id": error_id,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
            "path": request.url.path,
        }
    )

    # Don't expose internal error details in production
    if not settings.is_production:
        error_response["error"]["debug"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# Include routers
app.include_router(auth_router)
app.include_router(health_router)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information and status.
    """
    return {
        "message": "Overseer API is running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if not settings.is_production else "Documentation disabled in production",
        "health": "/health",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/info", tags=["root"])
async def api_info():
    """
    Detailed API information endpoint.
    """
    return {
        "name": "Overseer API",
        "description": "AI-Enabled Director Platform for Development Teams",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "features": {
            "authentication": True,
            "health_checks": True,
            "structured_logging": True,
            "request_correlation": True,
            "api_documentation": not settings.is_production,
        },
        "endpoints": {
            "authentication": "/auth",
            "health": "/health",
            "documentation": "/docs" if not settings.is_production else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    """
    logger.info(
        f"Overseer API starting up - Environment: {settings.ENVIRONMENT}, "
        f"Debug: {settings.DEBUG}, Version: 1.0.0"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    logger.info("Overseer API shutting down")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD and settings.is_development,
        log_config=None,  # Use our custom logging configuration
    )
