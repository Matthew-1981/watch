from __future__ import annotations
from typing import Optional, Any, Self

import datetime as dt
from math import sqrt
import sqlite3 as sl3

from .interpolation.base import InterpolationAbstract


class WatchDB:

    __slots__ = 'con', 'watch', 'cycle'

    def __init__(self, database_name: str):
        self.con = sl3.connect(database=database_name)
        self.watch: Optional[int] = None
        self.cycle: Optional[int] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.con.close()

    @staticmethod
    def create_watch_database(database_file: str):
        con = sl3.connect(database_file)
        con.execute('''
        CREATE TABLE info (
            watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50),
            date_of_joining DATETIME
        );
        ''')
        con.execute('''
        CREATE TABLE logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            watch_id INTEGER NOT NULL,
            cycle INTEGER NOT NULL,
            timedate DATETIME NOT NULL,
            measure FLOAT NOT NULL
        );
        ''')
        con.commit()
        con.close()

    def database_info(self) -> list[tuple]:
        cursor = self.con.execute('''
        SELECT i.watch_id, name, date_of_joining, COUNT(DISTINCT cycle), COUNT(measure)
        FROM info AS i LEFT JOIN logs AS l ON i.watch_id = l.watch_id
        GROUP BY date_of_joining, i.watch_id
        ORDER BY date_of_joining;
        ''')
        return cursor.fetchall().copy()

    def get_watch_name(self):
        if self.watch is None:
            return None
        cursor = self.con.execute("SELECT name FROM info WHERE watch_id = ?", (self.watch,))
        return cursor.fetchone()[0]

    def change_watch(self, id_: int or str):
        column = 'watch_id' if isinstance(id_, int) else 'name'
        cursor = self.con.execute(f'SELECT watch_id FROM info WHERE %s = ?;' % column, (id_,))
        count = tuple(cursor.fetchall())
        if len(count) == 1:
            self.watch = count[0][0]
            cursor = self.con.execute('SELECT MAX(cycle) FROM logs WHERE watch_id = ?', (self.watch,))
            count = cursor.fetchone()[0]
            if count is None:
                self.cycle = 1
            else:
                self.cycle = count
        else:
            raise ValueError(f"Watch with id {id_} does not exist")

    def change_cycle(self, cycle_number):
        cursor = self.con.execute('SELECT COUNT(*) FROM logs WHERE cycle = ?', (cycle_number,))
        count = cursor.fetchone()[0]
        if count > 0:
            self.cycle = cycle_number
        else:
            raise ValueError(f"Cycle {cycle_number} does not exist")

    def add_watch(self, name: str):
        now = dt.datetime.now()
        self.con.execute(
            '''
            INSERT INTO info (name, date_of_joining)
            VALUES (?, ?);
            ''',
            (name, now)
        )
        self.con.commit()

    def new_cycle(self):
        cursor = self.con.execute('SELECT MAX(cycle) FROM logs WHERE watch_id = ?', (self.watch,))
        count = cursor.fetchone()[0]
        self.cycle = count + 1

    def add_measure(self, measure: float):
        now = dt.datetime.now()
        self.con.execute(
            '''
            INSERT INTO logs (watch_id, cycle, timedate, measure)
            VALUES (?, ?, ?, ?)
            ''',
            (self.watch, self.cycle, now, measure)
        )
        self.con.commit()

    def del_current_watch(self):
        self.con.execute(
            "DELETE FROM logs WHERE watch_id = ?;",
            (self.watch,)
        )
        self.con.execute(
            "DELETE FROM info WHERE watch_id = ?;",
            (self.watch,)
        )
        self.watch = None
        self.cycle = None
        self.con.commit()

    def del_current_cycle(self):
        self.con.execute('DELETE FROM logs WHERE cycle = ? AND watch_id = ?', (self.cycle, self.watch))
        self.con.commit()
        self.change_watch(self.watch)

    def del_measure(self, log_id):
        cursor = self.con.execute(
            '''
            SELECT EXISTS(SELECT * FROM logs WHERE
                   log_id = ?
                   AND cycle = ?
                   AND watch_id = ?)
            ''',
            (log_id, self.cycle, self.watch)
        )
        if cursor.fetchone()[0] == 0:
            raise ValueError
        self.con.execute(
            'DELETE FROM logs WHERE log_id = ? AND cycle = ? AND watch_id = ?',
            (log_id, self.cycle, self.watch)
        )
        self.con.commit()

    @property
    def data(self) -> WatchLog:
        table: list[Record] = []
        cursor = self.con.execute(
            '''
            SELECT log_id, timedate, measure
            FROM logs
            WHERE watch_id = ? AND cycle = ?
            ORDER BY timedate;
            ''',
            (self.watch, self.cycle)
        )
        for row in cursor.fetchall():
            table.append(Record(time=dt.datetime.fromisoformat(row[1]), measure=row[2], id=row[0]))
        return WatchLog(table)


class Record:
    s_date = dt.datetime(dt.MINYEAR, 1, 1)

    def __init__(self, time: dt.datetime | float, measure: float, **other):
        self.time: dt.datetime
        if isinstance(time, (float, int)):
            self.time = self.s_date + dt.timedelta(seconds=time)
        else:
            self.time = time
        self.measure = measure
        self.other = other

    def __repr__(self):
        return f"{self.__class__.__name__}(time={repr(self.time)}, measure={self.measure}, **{self.other})"

    @property
    def time_as_float(self) -> float:
        return (self.time - self.s_date).total_seconds()

    def get_all(self) -> dict[str, Any]:
        return self.other | {"time": self.time, "measure": self.measure}


class WatchLog:

    __slots__ = 'data'

    def __init__(self, data: list[Record]):
        assert list(sorted(data, key=lambda x: x.time)) == data
        self.data: list[Record] = data.copy()

    def difference(self, index: int) -> float:
        if not (0 <= index < len(self.data)):
            raise IndexError("Index has to be 0 <= index < len(data).")
        if index == 0:
            return float('nan')
        current = self.data[index]
        previous = self.data[index - 1]
        return round(current.measure - previous.measure, 1)

    def get_log_with_dif(self) -> Self:
        table = []
        for i, entry in enumerate(self.data):
            table.append(Record(time=entry.time, measure=entry.measure, difference=self.difference(i), **entry.other))
        return self.__class__(table)

    def fill(self, interpolation_method: type[InterpolationAbstract]) -> Self:
        SECONDS_IN_DAY = 24 * 60 * 60

        data = [(record.time_as_float, record.measure) for record in self.data]
        if len(self.data) == 0:
            return self.__class__([])

        f = interpolation_method(data).calculate()
        start = int(self.data[0].time_as_float)
        end = int(self.data[-1].time_as_float)

        table = []
        for time in range(start, end + 1, SECONDS_IN_DAY):
            table.append(Record(time=time, measure=round(f(time), 1)))

        return self.__class__(table)

    @property
    def average(self) -> float:
        data = [self.difference(i) for i in range(1, len(self.data))]
        return round(sum(data) / len(data), 2)

    @property
    def standard_deviation(self) -> float:
        data = [self.difference(i) for i in range(1, len(self.data))]
        avg = self.average
        return round(sqrt(sum((x - avg)**2 for x in data) / len(data)), 2)

    @property
    def delta(self) -> float:
        data = [self.difference(i) for i in range(1, len(self.data))]
        return round(max(data) - min(data), 2)
