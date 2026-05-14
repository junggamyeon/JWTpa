from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from jwtpa.database.database_manager import DatabaseManager

if TYPE_CHECKING:
    from endstone.level import Location


@dataclass(frozen=True, slots=True)
class TPARequest:
    id: int
    sender_uuid: str
    sender_name: str
    receiver_uuid: str
    receiver_name: str
    world: str | None
    x: float | None
    y: float | None
    z: float | None
    pitch: float | None
    yaw: float | None
    created_at: str
    expires_at: str


class TPARequestRepository:

    def __init__(self, db: DatabaseManager, timeout_seconds: int = 60) -> None:
        self._db = db
        self._timeout = timeout_seconds

    async def create_request(
        self,
        sender_uuid: str,
        sender_name: str,
        receiver_uuid: str,
        receiver_name: str,
        world: str | None = None,
        x: float | None = None,
        y: float | None = None,
        z: float | None = None,
        yaw: float | None = None,
        pitch: float | None = None,
    ) -> int:
        now = datetime.now()
        expires = now + timedelta(seconds=self._timeout)
        expires_str = expires.strftime("%Y-%m-%d %H:%M:%S")

        cursor = await self._db.execute(
            """
            INSERT INTO tpa_requests
            (sender_uuid, sender_name, receiver_uuid, receiver_name, world, x, y, z, pitch, yaw, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sender_uuid,
                sender_name,
                receiver_uuid,
                receiver_name,
                world,
                x,
                y,
                z,
                pitch,
                yaw,
                expires_str,
            ),
        )
        return cursor.lastrowid

    async def get_active_request_by_sender(self, sender_uuid: str) -> TPARequest | None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = await self._db.fetchone(
            """
            SELECT id, sender_uuid, sender_name, receiver_uuid, receiver_name,
                   world, x, y, z, pitch, yaw, created_at, expires_at
            FROM tpa_requests
            WHERE sender_uuid = ? AND expires_at > ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (sender_uuid, now),
        )
        return self._row_to_request(row)

    async def get_active_request_for_receiver(self, receiver_uuid: str) -> TPARequest | None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = await self._db.fetchone(
            """
            SELECT id, sender_uuid, sender_name, receiver_uuid, receiver_name,
                   world, x, y, z, pitch, yaw, created_at, expires_at
            FROM tpa_requests
            WHERE receiver_uuid = ? AND expires_at > ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (receiver_uuid, now),
        )
        return self._row_to_request(row)

    async def delete_request(self, request_id: int) -> None:
        await self._db.execute("DELETE FROM tpa_requests WHERE id = ?", (request_id,))

    async def delete_expired_requests(self) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = await self._db.execute(
            "DELETE FROM tpa_requests WHERE expires_at <= ?",
            (now,),
        )
        return cursor.rowcount

    async def has_active_request(self, sender_uuid: str, receiver_uuid: str) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        val = await self._db.fetchval(
            """
            SELECT 1 FROM tpa_requests
            WHERE sender_uuid = ? AND receiver_uuid = ? AND expires_at > ?
            """,
            (sender_uuid, receiver_uuid, now),
        )
        return val is not None

    def _row_to_request(self, row) -> TPARequest | None:
        if row is None:
            return None
        return TPARequest(
            id=row["id"],
            sender_uuid=row["sender_uuid"],
            sender_name=row["sender_name"],
            receiver_uuid=row["receiver_uuid"],
            receiver_name=row["receiver_name"],
            world=row["world"],
            x=row["x"],
            y=row["y"],
            z=row["z"],
            pitch=row["pitch"],
            yaw=row["yaw"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )
