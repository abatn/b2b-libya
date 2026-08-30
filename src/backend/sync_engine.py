"""
Libya B2B Platform - Delta-Sync Engine
Sprint 4: Offline-First Synchronisation
Projektversion: v1.4

CPU-basiert, Open-Source (MIT)
Fuer 77,4% Stromzugang und 31 Mbps Mobile (World Bank 2024, Ookla 2026)
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# SYNC STATUS
# ============================================================


class SyncStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================
# SYNC ENTRY
# ============================================================


@dataclass
class SyncEntry:
    """Einzelner Sync-Eintrag"""

    id: str
    table_name: str
    record_id: int
    action: str  # create, update, delete
    data: Dict[str, Any]
    checksum: str
    timestamp: str
    status: SyncStatus = SyncStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3


# ============================================================
# DELTA-SYNC ENGINE
# ============================================================


class DeltaSyncEngine:
    """
    Delta-Sync-Engine fuer Offline-First Plattform

    Features:
    - Nur geaenderte Daten synchronisieren (Delta)
    - Konfliktloesung (Last-Write-Wins)
    - Offline-Speicherung
    - Automatischer Retry
    - Checksum-Validierung

    Begruendung:
    - 77,4% Stromzugang (World Bank 2024)
    - 31 Mbps Mobile (Ookla 2026)
    - Instabile Internetverbindung
    """

    def __init__(self, db_path: str = ":memory:"):
        """
        Delta-Sync-Engine initialisieren.

        Args:
            db_path: Pfad zur lokalen SQLite-Datenbank
        """
        self.db_path = db_path
        self.local_db = sqlite3.connect(db_path, check_same_thread=False)
        self._create_sync_tables()
        self.pending_syncs: List[SyncEntry] = []
        self.last_sync_time: Optional[datetime] = None

    def _create_sync_tables(self):
        """Sync-Tabellen in lokaler DB erstellen"""
        cursor = self.local_db.cursor()

        # Sync-Log Tabelle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                id TEXT PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                data TEXT NOT NULL,
                checksum TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sync-Metadaten
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.local_db.commit()

    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Checksum fuer Daten berechnen"""
        data_string = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_string.encode()).hexdigest()

    def create_sync_entry(
        self, table_name: str, record_id: int, action: str, data: Dict[str, Any]
    ) -> SyncEntry:
        """
        Neuen Sync-Eintrag erstellen.

        Args:
            table_name: Name der Tabelle
            record_id: ID des Datensatzes
            action: Aktion (create, update, delete)
            data: Daten des Datensatzes

        Returns:
            SyncEntry Objekt
        """

        entry_id = f"{table_name}_{record_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        checksum = self.calculate_checksum(data)

        entry = SyncEntry(
            id=entry_id,
            table_name=table_name,
            record_id=record_id,
            action=action,
            data=data,
            checksum=checksum,
            timestamp=datetime.now().isoformat(),
        )

        # In lokaler DB speichern
        cursor = self.local_db.cursor()
        cursor.execute(
            """
            INSERT INTO sync_log (
                id, table_name, record_id, action,
                data, checksum, timestamp, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                entry.id,
                entry.table_name,
                entry.record_id,
                entry.action,
                json.dumps(entry.data, ensure_ascii=False),
                entry.checksum,
                entry.timestamp,
                entry.status.value,
            ),
        )

        self.local_db.commit()

        # Zu Pending-Liste hinzufuegen
        self.pending_syncs.append(entry)

        return entry

    def get_pending_syncs(self) -> List[SyncEntry]:
        """Alle ausstehenden Syncs abrufen"""
        cursor = self.local_db.cursor()
        cursor.execute("""
            SELECT id, table_name, record_id, action, data, checksum, timestamp, status, retry_count
            FROM sync_log
            WHERE status = 'pending'
            ORDER BY timestamp ASC
        """)

        rows = cursor.fetchall()
        entries = []

        for row in rows:
            entry = SyncEntry(
                id=row[0],
                table_name=row[1],
                record_id=row[2],
                action=row[3],
                data=json.loads(row[4]),
                checksum=row[5],
                timestamp=row[6],
                status=SyncStatus(row[7]),
                retry_count=row[8],
            )
            entries.append(entry)

        return entries

    def sync_entry(self, entry: SyncEntry) -> Tuple[bool, str]:
        """
        Einzelnen Sync-Eintrag synchronisieren.

        In der Praxis: HTTP-Request an Server
        Hier: Simulation mit Validierung

        Returns:
            Tuple aus (Erfolg, Nachricht)
        """

        # Checksum validieren
        current_checksum = self.calculate_checksum(entry.data)
        if current_checksum != entry.checksum:
            return False, "Checksum mismatch - Daten wurden geaendert"

        # Simulierter Sync (in Produktion: HTTP POST)
        # Erfolg: 95% bei erstem Versuch
        import random

        success = random.random() < 0.95

        if success:
            # Status aktualisieren
            cursor = self.local_db.cursor()
            cursor.execute(
                """
                UPDATE sync_log SET status = 'completed' WHERE id = ?
            """,
                (entry.id,),
            )
            self.local_db.commit()

            return True, "Sync erfolgreich"
        else:
            # Retry-Zaehler erhoehen
            entry.retry_count += 1

            if entry.retry_count >= entry.max_retries:
                cursor = self.local_db.cursor()
                cursor.execute(
                    """
                    UPDATE sync_log SET status = 'failed', retry_count = ? WHERE id = ?
                """,
                    (entry.retry_count, entry.id),
                )
                self.local_db.commit()

                return False, f"Sync fehlgeschlagen nach {entry.max_retries} Versuchen"
            else:
                cursor = self.local_db.cursor()
                cursor.execute(
                    """
                    UPDATE sync_log SET retry_count = ? WHERE id = ?
                """,
                    (entry.retry_count, entry.id),
                )
                self.local_db.commit()

                return (
                    False,
                    f"Sync fehlgeschlagen, Versuch {entry.retry_count}/{entry.max_retries}",
                )

    def sync_all_pending(self) -> Dict[str, Any]:
        """
        Alle ausstehenden Syncs synchronisieren.

        Returns:
            Zusammenfassung des Syncs
        """
        pending = self.get_pending_syncs()

        results = {"total": len(pending), "success": 0, "failed": 0, "errors": []}

        for entry in pending:
            success, message = self.sync_entry(entry)

            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({"id": entry.id, "error": message})

        # Letzten Sync-Zeitpunkt aktualisieren
        self.last_sync_time = datetime.now()
        self._update_metadata("last_sync", self.last_sync_time.isoformat())

        return results

    def get_changes_since(self, since: datetime) -> List[SyncEntry]:
        """
        Alle Aenderungen seit einem bestimmten Zeitpunkt abrufen.

        Args:
            since: Zeitpunkt seit dem gesucht wird

        Returns:
            Liste der SyncEntries
        """
        cursor = self.local_db.cursor()
        cursor.execute(
            """
            SELECT id, table_name, record_id, action, data, checksum, timestamp, status, retry_count
            FROM sync_log
            WHERE timestamp > ? AND status = 'completed'
            ORDER BY timestamp ASC
        """,
            (since.isoformat(),),
        )

        rows = cursor.fetchall()
        entries = []

        for row in rows:
            entry = SyncEntry(
                id=row[0],
                table_name=row[1],
                record_id=row[2],
                action=row[3],
                data=json.loads(row[4]),
                checksum=row[5],
                timestamp=row[6],
                status=SyncStatus(row[7]),
                retry_count=row[8],
            )
            entries.append(entry)

        return entries

    def resolve_conflict(
        self, local_entry: SyncEntry, remote_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Konfliktloesung (Last-Write-Wins).

        Args:
            local_entry: Lokaler Sync-Eintrag
            remote_data: Remote-Daten

        Returns:
            Gewinner-Daten
        """

        local_timestamp = datetime.fromisoformat(local_entry.timestamp)
        remote_timestamp = datetime.now()  # In Produktion: vom Remote-Server

        if local_timestamp > remote_timestamp:
            return local_entry.data
        else:
            return remote_data

    def get_sync_stats(self) -> Dict[str, Any]:
        """Sync-Statistiken abrufen"""
        cursor = self.local_db.cursor()

        # Gesamtanzahl
        cursor.execute("SELECT COUNT(*) FROM sync_log")
        total = cursor.fetchone()[0]

        # Nach Status
        cursor.execute("SELECT status, COUNT(*) FROM sync_log GROUP BY status")
        status_counts = dict(cursor.fetchall())

        # Nach Tabelle
        cursor.execute("SELECT table_name, COUNT(*) FROM sync_log GROUP BY table_name")
        table_counts = dict(cursor.fetchall())

        return {
            "total_entries": total,
            "by_status": status_counts,
            "by_table": table_counts,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
        }

    def _update_metadata(self, key: str, value: str):
        """Metadaten aktualisieren"""
        cursor = self.local_db.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
            VALUES (?, ?, ?)
        """,
            (key, value, datetime.now().isoformat()),
        )
        self.local_db.commit()

    def get_metadata(self, key: str) -> Optional[str]:
        """Metadaten abrufen"""
        cursor = self.local_db.cursor()
        cursor.execute("SELECT value FROM sync_metadata WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None

    def clear_completed_syncs(self) -> int:
        """Abgeschlossene Syncs loeschen"""
        cursor = self.local_db.cursor()
        cursor.execute("DELETE FROM sync_log WHERE status = 'completed'")
        deleted = cursor.rowcount
        self.local_db.commit()
        return deleted


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_sync_engine_instance = None


def get_sync_engine(db_path: str = ":memory:") -> DeltaSyncEngine:
    """Singleton-Instanz der Sync-Engine"""
    global _sync_engine_instance
    if _sync_engine_instance is None:
        _sync_engine_instance = DeltaSyncEngine(db_path)
    return _sync_engine_instance
