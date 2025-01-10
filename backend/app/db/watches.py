from datetime import datetime
from typing import Self

from pydantic import BaseModel
from mysql.connector.aio.cursor import MySQLCursor
from mysql.connector import Error

from .exceptions import OperationError, ConstraintError


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
        try:
            await cursor.execute(
                "UPDATE watch SET user_id = %s, name = %s, date_of_creation = %s WHERE watch_id = %s",
                (self.data.user_id, self.data.name, self.data.date_of_creation, self.data.watch_id)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()

    async def delete(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "DELETE FROM watch WHERE watch_id = %s",
                (self.data.watch_id,)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()

    @classmethod
    async def get_watch_by_id(cls, cursor: MySQLCursor, watch_id: int) -> Self:
        await cursor.execute("SELECT * FROM watch WHERE watch_id = %s", (watch_id,))
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
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
            raise OperationError()
        watch = ExistingWatch(
            watch_id=row[0],
            user_id=row[1],
            name=row[2],
            date_of_creation=row[3]
        )
        return cls(watch)

    @classmethod
    async def new_watch(cls, cursor: MySQLCursor, watch: NewWatch) -> Self:
        try:
            await cursor.execute(
                "INSERT INTO watch (user_id, name, date_of_creation) VALUES (%s, %s, %s)",
                (watch.user_id, watch.name, watch.date_of_creation)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()
        return await cls.get_watch_by_name(cursor, watch.user_id, watch.name)


class NewLog(BaseModel):
    watch_id: int
    cycle: int
    timedate: datetime
    measure: float


class ExistingLog(NewLog):
    log_id: int


class LogRecord:

    def __init__(self, row: ExistingLog):
        self._initial_ids = (row.watch_id, row.log_id)
        self.data = row

    def check_integrity(self) -> bool:
        return self._initial_ids == (self.data.watch_id, self.data.log_id)

    async def update(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "UPDATE log SET watch_id = %s, cycle = %s, timedate = %s, measure = %s WHERE log_id = %s",
                (self.data.watch_id, self.data.cycle, self.data.timedate, self.data.measure, self.data.log_id)
            )
        except Error as e:
            raise ConstraintError from e
        if cursor.rowcount != 1:
            raise OperationError()

    async def delete(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        await cursor.execute(
            "DELETE FROM log WHERE log_id = %s",
            (self.data.log_id,)
        )
        if cursor.rowcount != 1:
            raise OperationError()

    @classmethod
    async def get_log_by_id(cls, cursor: MySQLCursor, log_id: int) -> Self:
        await cursor.execute("SELECT * FROM log WHERE log_id = %s", (log_id,))
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        log = ExistingLog(
            log_id=row[0],
            watch_id=row[1],
            cycle=row[2],
            timedate=row[3],
            measure=row[4]
        )
        return cls(log)

    @classmethod
    async def new_log(cls, cursor: MySQLCursor, log: NewLog) -> Self:
        try:
            await cursor.execute(
                "INSERT INTO log (watch_id, cycle, timedate, measure) VALUES (%s, %s, %s, %s)",
                (log.watch_id, log.cycle, log.timedate, log.measure)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()
        return await cls.get_log_by_id(cursor, cursor.lastrowid)

    @classmethod
    async def get_logs(cls, cursor: MySQLCursor, watch_id: int, cycle: int) -> tuple[Self, ...]:
        await cursor.execute(
            "SELECT * FROM log WHERE watch_id = %s AND cycle = %s",
            (watch_id, cycle)
        )
        rows = await cursor.fetchall()
        out = []
        for row in rows:
            current = ExistingLog(
                log_id=row[0],
                watch_id=row[1],
                cycle=row[2],
                timedate=row[3],
                measure=row[4]
            )
            out.append(cls(current))
        return tuple(out)

    @classmethod
    async def delete_logs(cls, cursor: MySQLCursor, watch_id: int, cycle: int):
        await cursor.execute(
            "DELETE FROM log WHERE watch_id = %s AND cycle = %s",
            (watch_id, cycle)
        )
        if cursor.rowcount == -1:
            raise OperationError()
