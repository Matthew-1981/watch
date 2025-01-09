from datetime import datetime
from typing import Self

from pydantic import BaseModel
from mysql.connector.aio.cursor import MySQLCursor

from .common import DatabaseError


class NewWatch(BaseModel):
    user_id: int
    name: str
    date_of_creation: datetime


class ExistingWatch(NewWatch):
    watch_id: int


class WatchRecord:

    def __init__(self, row: ExistingWatch):
        self._initial_ids = (row.user_id, row.watch_id)
        self.data = row

    def check_integrity(self) -> bool:
        return self._initial_ids == (self.data.user_id, self.data.watch_id)

    async def update(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        await cursor.execute(
            "UPDATE watch SET user_id = %s, name = %s, date_of_creation = %s WHERE watch_id = %s",
            (self.data.user_id, self.data.name, self.data.date_of_creation, self.data.watch_id)
        )
        if cursor.rowcount != 1:
            raise DatabaseError()

    async def delete(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        await cursor.execute(
            "DELETE FROM watch WHERE watch_id = %s",
            (self.data.watch_id,)
        )
        if cursor.rowcount != 1:
            raise DatabaseError()

    @classmethod
    async def get_watch_by_id(cls, cursor: MySQLCursor, watch_id: int) -> Self:
        await cursor.execute("SELECT * FROM watch WHERE watch_id = %s", (watch_id,))
        row = await cursor.fetchone()
        if row is None:
            raise DatabaseError()
        watch = ExistingWatch(
            watch_id=row[0],
            user_id=row[1],
            name=row[2],
            date_of_creation=row[3]
        )
        return cls(watch)

    @classmethod
    async def get_watch_by_name(cls, cursor: MySQLCursor, user_id: int, name: str) -> Self:
        await cursor.execute("SELECT * FROM watch WHERE user_id = %s AND name = %s", (user_id, name))
        row = await cursor.fetchone()
        if row is None:
            raise DatabaseError()
        watch = ExistingWatch(
            watch_id=row[0],
            user_id=row[1],
            name=row[2],
            date_of_creation=row[3]
        )
        return cls(watch)

    @classmethod
    async def new_watch(cls, cursor: MySQLCursor, watch: NewWatch) -> Self:
        await cursor.execute(
            "INSERT INTO watch (user_id, name, date_of_creation) VALUES (%s, %s, %s)",
            (watch.user_id, watch.name, watch.date_of_creation)
        )
        if cursor.rowcount != 1:
            raise DatabaseError()
        return await cls.get_watch_by_name(cursor, watch.user_id, watch.name)
