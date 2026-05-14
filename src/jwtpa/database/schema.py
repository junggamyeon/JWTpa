from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone import Logger
    from jwtpa.database.database_manager import DatabaseManager


class SchemaManager:

    def __init__(self, db: DatabaseManager, logger: Logger) -> None:
        self._db = db
        self._logger = logger

    async def create_tables(self) -> None:
        await self._create_tpa_requests_table()

    async def _create_tpa_requests_table(self) -> None:
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS tpa_requests (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_uuid     TEXT NOT NULL,
                sender_name     TEXT NOT NULL,
                receiver_uuid   TEXT NOT NULL,
                receiver_name   TEXT NOT NULL,
                world           TEXT,
                x               REAL,
                y               REAL,
                z               REAL,
                pitch           REAL,
                yaw             REAL,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at      TEXT NOT NULL
            );
        """)
