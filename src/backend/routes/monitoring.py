"""
Libya B2B Platform - Monitoring Routes
"""

import time
from datetime import datetime, timezone

from fastapi import APIRouter

from config import IS_POSTGRES

router = APIRouter(tags=["monitoring"])

_DB_LABEL = "postgresql" if IS_POSTGRES else "sqlite"


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": _DB_LABEL,
        "offline_capable": not IS_POSTGRES,
    }


@router.get("/")
def root():
    return {"name": "Libya B2B Platform API", "version": "2.0.0", "docs": "/docs"}


@router.get("/api/monitoring/stats")
def get_monitoring_stats():
    import psutil

    uptime_seconds = time.time() - _start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return {
        "uptime": f"{hours}h {minutes}m",
        "uptime_seconds": int(uptime_seconds),
        "requests_total": _request_count,
        "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
        "memory_usage_percent": psutil.virtual_memory().percent,
        "memory_used_mb": round(psutil.virtual_memory().used / 1024 / 1024, 2),
        "disk_usage_percent": psutil.disk_usage("/").percent,
        "active_processes": len(psutil.pids()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }


@router.get("/api/monitoring/health-detailed")
def get_detailed_health():
    import psutil

    return {
        "status": "healthy",
        "database": _DB_LABEL,
        "offline_capable": not IS_POSTGRES,
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
        "memory_available_gb": round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Module-level counters for monitoring (importable)
_start_time = time.time()
_request_count = 0
