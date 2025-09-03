"""
Health check endpoints for Overseer API services.

This module provides comprehensive health checks for all system components
including database, Redis, and external service dependencies.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, engine
from config.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)
settings = get_settings()


async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and basic operations.

    Returns:
        Dict containing database health status
    """
    try:
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

            # Test table access
            tables_result = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in tables_result]

            return {
                "status": "healthy",
                "response_time_ms": 0,  # Would measure actual time in production
                "tables_count": len(tables),
                "tables": tables[:5],  # Show first 5 tables
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def check_redis() -> Dict[str, Any]:
    """
    Check Redis connectivity and basic operations.

    Returns:
        Dict containing Redis health status
    """
    try:
        # For now, return a placeholder since Redis isn't set up yet
        # In a real implementation, this would test Redis connectivity
        return {
            "status": "not_configured",
            "message": "Redis not yet configured",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/")
async def health_overview():
    """
    Comprehensive health check for all system components.

    Returns:
        Overall system health status
    """
    start_time = datetime.utcnow()

    # Run all health checks concurrently
    database_health, redis_health = await asyncio.gather(
        check_database(),
        check_redis(),
        return_exceptions=True
    )

    # Handle exceptions from health checks
    if isinstance(database_health, Exception):
        database_health = {
            "status": "error",
            "error": str(database_health),
            "timestamp": datetime.utcnow().isoformat()
        }

    if isinstance(redis_health, Exception):
        redis_health = {
            "status": "error",
            "error": str(redis_health),
            "timestamp": datetime.utcnow().isoformat()
        }

    # Determine overall health
    overall_status = "healthy"
    if database_health["status"] != "healthy":
        overall_status = "degraded" if database_health["status"] == "not_configured" else "unhealthy"
    if redis_health["status"] not in ["healthy", "not_configured"]:
        overall_status = "unhealthy"

    end_time = datetime.utcnow()
    response_time = (end_time - start_time).total_seconds() * 1000

    return {
        "status": overall_status,
        "timestamp": end_time.isoformat(),
        "response_time_ms": round(response_time, 2),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": database_health,
            "redis": redis_health,
            "api": {
                "status": "healthy",
                "timestamp": end_time.isoformat()
            }
        }
    }


@router.get("/database")
async def health_database():
    """
    Detailed database health check.

    Returns:
        Database-specific health information
    """
    result = await check_database()

    if result["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result
        )

    return result


@router.get("/redis")
async def health_redis():
    """
    Detailed Redis health check.

    Returns:
        Redis-specific health information
    """
    result = await check_redis()

    if result["status"] not in ["healthy", "not_configured"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result
        )

    return result


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness check.

    Returns:
        Simple ready/not ready status
    """
    database_health = await check_database()

    if database_health["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"ready": False, "reason": "Database not available"}
        )

    return {"ready": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness check.

    Returns:
        Simple alive/dead status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": 0  # Would track actual uptime in production
    }
