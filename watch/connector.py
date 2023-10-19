
import datetime as dt
import sqlite3 as sl3
from typing import Optional

from interpolation.base import InterpolationAbstract


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
    def data(self):
        return WatchLog(self)


class Record(tuple):
    s_date = dt.datetime(dt.MINYEAR, 1, 1)

    def __new__(cls, id_, timedate: dt.datetime, measure: float, difference: float | None | str = ''):
        if difference == '':
            return super().__new__(cls, (id_, timedate, measure))
        else:
            return super().__new__(cls, (id_, timedate, measure, difference))

    def plus_diff(self, difference: float | None):
        return Record(self.id, self.timedate, self.measure, difference)

    @property
    def id(self) -> int:
        return self[0]

    @property
    def timedate(self) -> dt.datetime:
        return self[1]

    @property
    def measure(self) -> float:
        return self[2]

    @property
    def difference(self) -> Optional[float]:
        if len(self) == 3:
            raise Exception
        return self[3]

    @property
    def as_floats(self) -> tuple[float, float]:
        return (self.timedate - self.s_date).total_seconds(), self.measure


class WatchLog:

    __slots__ = 'database', 'watch', 'cycle', 'data'

    def __init__(self, database: WatchDB):
        table: list[Record] = []
        cursor = database.con.execute(
            '''
            SELECT log_id, timedate, measure
            FROM logs
            WHERE watch_id = ? AND cycle = ?
            ORDER BY timedate;
            ''',
            (database.watch, database.cycle)
        )
        for row in cursor.fetchall():
            table.append(Record(row[0], dt.datetime.fromisoformat(row[1]), row[2]))

        self.database = database
        self.watch = database.watch
        self.cycle = database.cycle
        self.data: tuple[Record] = tuple(table)

    def difference(self):
        if len(self.data) == 0:
            raise Exception

        out = [self.data[0].plus_diff(None)]
        for w in range(1, len(self.data)):
            out.append(self.data[w].plus_diff(round(self.data[w].measure - self.data[w - 1].measure, 1)))

        return out

    def _record_to_float(self) -> list[tuple[float, float]]:
        return [item.as_floats for item in self.data]

    def fill(self, interpolation_method: type[InterpolationAbstract]):
        data = self._record_to_float()
        f = interpolation_method(data).calculate()
        seconds_in_day = 24 * 60 * 60
        start: dt.datetime = self.data[0].timedate
        end: dt.datetime = self.data[-1].timedate
        out = [Record(-1, start, self.data[0].measure, None)]
        i = 1

        while start + dt.timedelta(seconds=seconds_in_day * i) <= end:
            tm = start + dt.timedelta(seconds=seconds_in_day * i)
            cur_calc = round(f((tm - Record.s_date).total_seconds()), 1)
            tmp = Record(
                -1,
                start + dt.timedelta(seconds=seconds_in_day * i),
                cur_calc,
                round(cur_calc - out[-1].measure, 1)
            )
            out.append(tmp)
            i += 1

        return out

    def stats(self, interpolation_method: type[InterpolationAbstract]) -> dict:
        out = {}
        data = [w.difference for w in self.fill(interpolation_method)[1:]]
        out['average'] = round(sum(data)/len(data), 2)
        out['delta'] = round(max(data) - min(data), 2)
        out['median'] = sorted(data)[len(data)//2]
        return out
