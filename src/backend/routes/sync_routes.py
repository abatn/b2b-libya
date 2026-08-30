"""
Libya B2B Platform - Sync Routes
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/delta")
def delta_sync(table_name: str, record_id: int, action: str, data: Dict[str, Any]):
    from sync_engine import get_sync_engine

    engine = get_sync_engine()
    entry = engine.create_sync_entry(
        table_name=table_name, record_id=record_id, action=action, data=data
    )
    return {"entry_id": entry.id, "status": entry.status.value, "checksum": entry.checksum}


@router.post("/all")
def sync_all_pending():
    from sync_engine import get_sync_engine

    return get_sync_engine().sync_all_pending()


@router.get("/stats")
def get_sync_stats():
    from sync_engine import get_sync_engine

    return get_sync_engine().get_sync_stats()


@router.get("/changes")
def get_sync_changes(since: Optional[str] = None):
    from sync_engine import get_sync_engine

    engine = get_sync_engine()
    if since:
        since_dt = datetime.fromisoformat(since)
        changes = engine.get_changes_since(since_dt)
    else:
        changes = engine.get_pending_syncs()
    return {
        "changes": [
            {
                "table": e.table_name,
                "record_id": e.record_id,
                "action": e.action,
                "timestamp": e.timestamp,
            }
            for e in changes
        ],
        "count": len(changes),
    }


@router.get("/pending")
def get_pending_syncs():
    from sync_engine import get_sync_engine

    engine = get_sync_engine()
    pending = engine.get_pending_syncs()
    return {
        "pending": [{"id": e.id, "table": e.table_name, "record_id": e.record_id} for e in pending],
        "count": len(pending),
    }


@router.delete("/completed")
def clear_completed_syncs():
    from sync_engine import get_sync_engine

    deleted = get_sync_engine().clear_completed_syncs()
    return {"deleted": deleted}
