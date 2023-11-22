from __future__ import annotations
from typing import Optional

import datetime as dt
import sqlite3 as sl3

from .log import Record, WatchLog


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

    def change_watch(self, id_: int | str):
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
        out = self.con.execute("SELECT * FROM info WHERE name = ?", (name,))
        if len(out.fetchall()) != 0:
            raise ValueError("Watch already in database")
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
