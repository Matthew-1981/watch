from datetime import datetime, timezone

from pydantic import BaseModel
from mysql.connector.aio.cursor import MySQLCursor
from mysql.connector import Error

from .exceptions import OperationError, ConstraintError
from .users import UserRecord


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

    async def update(self, cursor: MySQLCursor) -> int:
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "UPDATE watch SET user_id = %s, name = %s, date_of_creation = %s WHERE watch_id = %s",
                (self.data.user_id, self.data.name, self.data.date_of_creation, self.data.watch_id)
            )
        except Error as e:
            raise ConstraintError() from e
        return cursor.rowcount

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


class WatchRecordManager:

    def __init__(self, user: UserRecord):
        self.user = user

    async def get_all_watches(self, cursor: MySQLCursor) -> tuple[WatchRecord, ...]:
        await cursor.execute("SELECT * FROM watch WHERE user_id = %s ORDER BY date_of_creation ASC",
                             (self.user.data.user_id,))
        rows = await cursor.fetchall()
        out = []
        for row in rows:
            current = ExistingWatch(
                watch_id=row[0],
                user_id=row[1],
                name=row[2],
                date_of_creation=row[3].replace(tzinfo=timezone.utc)
            )
            out.append(WatchRecord(current))
        return tuple(out)

    async def get_watch_by_name(self, cursor: MySQLCursor, name: str) -> WatchRecord:
        await cursor.execute(
            "SELECT * FROM watch WHERE user_id = %s AND name = %s",
            (self.user.data.user_id, name)
        )
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        watch = ExistingWatch(
            watch_id=row[0],
            user_id=row[1],
            name=row[2],
            date_of_creation=row[3].replace(tzinfo=timezone.utc)
        )
        return WatchRecord(watch)

    async def new_watch(self, cursor: MySQLCursor, watch: NewWatch) -> WatchRecord:
        if self.user.data.user_id != watch.user_id:
            raise ValueError("User in 'watch' is different than the one in self.user")
        try:
            await cursor.execute(
                "INSERT INTO watch (user_id, name, date_of_creation) VALUES (%s, %s, %s)",
                (watch.user_id, watch.name, watch.date_of_creation)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()
        return await self.get_watch_by_name(cursor, watch.name)


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

    async def update(self, cursor: MySQLCursor) -> int:
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "UPDATE log SET watch_id = %s, cycle = %s, timedate = %s, measure = %s WHERE log_id = %s",
                (self.data.watch_id, self.data.cycle, self.data.timedate, self.data.measure, self.data.log_id)
            )
        except Error as e:
            raise ConstraintError from e
        return cursor.rowcount

    async def delete(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        await cursor.execute(
            "DELETE FROM log WHERE log_id = %s",
            (self.data.log_id,)
        )
        if cursor.rowcount != 1:
            raise OperationError()


class LogRecordManager:

    def __init__(self, watch: WatchRecord):
        self.watch = watch

    async def get_log_by_id(self, cursor: MySQLCursor, cycle: int, log_id: int) -> LogRecord:
        await cursor.execute(
            "SELECT * FROM log WHERE log_id = %s AND watch_id = %s AND cycle = %s",
            (log_id, self.watch.data.watch_id, cycle)
        )
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        log = ExistingLog(
            log_id=row[0],
            watch_id=row[1],
            cycle=row[2],
            timedate=row[3].replace(tzinfo=timezone.utc),
            measure=row[4]
        )
        return LogRecord(log)

    async def new_log(self, cursor: MySQLCursor, cycle: int, log: NewLog) -> LogRecord:
        if self.watch.data.watch_id != log.watch_id or cycle != log.cycle:
            raise ValueError("self.watch or cycle are different in log: NewLog")
        try:
            await cursor.execute(
                "INSERT INTO log (watch_id, cycle, timedate, measure) VALUES (%s, %s, %s, %s)",
                (log.watch_id, log.cycle, log.timedate, log.measure)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()
        log_id = cursor.lastrowid
        assert log_id is not None
        return await self.get_log_by_id(cursor, cycle, log_id)

    async def get_cycles(self, cursor: MySQLCursor) ->  list[int]:
        await cursor.execute(
            "SELECT DISTINCT cycle FROM log WHERE watch_id = %s ORDER BY cycle ASC",
            (self.watch.data.watch_id,)
        )
        return [i for (i,) in await cursor.fetchall()]


    async def get_logs(self, cursor: MySQLCursor, cycle: int) -> tuple[LogRecord, ...]:
        await cursor.execute(
            "SELECT * FROM log WHERE watch_id = %s AND cycle = %s",
            (self.watch.data.watch_id, cycle)
        )
        rows = await cursor.fetchall()
        out = []
        for row in rows:
            current = ExistingLog(
                log_id=row[0],
                watch_id=row[1],
                cycle=row[2],
                timedate=row[3].replace(tzinfo=timezone.utc),
                measure=row[4]
            )
            out.append(LogRecord(current))
        return tuple(out)

    async def delete_logs(self, cursor: MySQLCursor, cycle: int):
        await cursor.execute(
            "DELETE FROM log WHERE watch_id = %s AND cycle = %s",
            (self.watch.data.watch_id, cycle)
        )
        if cursor.rowcount == -1:
            raise OperationError()
