from __future__ import annotations
from typing import Any

import datetime as dt
from math import sqrt

from .interpolation import InterpolationAbstract


class Record(dict):
    s_date = dt.datetime(dt.MINYEAR, 1, 1)

    def __init__(self, datetime: dt.datetime | float, measure: float, **other):
        if isinstance(datetime, (float, int)):
            datetime = self.s_date + dt.timedelta(seconds=datetime)
        super().__init__({'datetime': datetime, 'measure': measure, **other})

    @classmethod
    def from_row(cls, headers: tuple[str], row: tuple[Any, ...]) -> Record:
        if 'datetime' not in headers or 'measure' not in headers:
            raise ValueError("Headers must contain 'datetime' and 'measure'.")
        return cls(**{header: value for header, value in zip(headers, row)})

    @property
    def datetime(self) -> dt.datetime:
        return self['datetime']

    @property
    def measure(self) -> float:
        return self['measure']

    @property
    def other(self) -> dict[str, Any]:
        return {k: v for k, v in self.items() if k not in ('datetime', 'measure')}

    def __repr__(self):
        return f"{self.__class__.__name__}(time={repr(self.datetime)}, measure={self.measure}, **{self.other})"

    @property
    def time_as_float(self) -> float:
        return (self.datetime - self.s_date).total_seconds()


class WatchLogFrame:

    __slots__ = 'data'

    def __init__(self, data: list[Record]):
        assert list(sorted(data, key=lambda x: x.datetime)) == data
        self.data: list[Record] = data.copy()

    @classmethod
    def from_table(cls, headers: tuple[str], table: list[tuple[Any, ...]]) -> WatchLogFrame:
        return cls([Record.from_row(headers, row) for row in table])

    def difference(self, index: int) -> float | None:
        if not (0 <= index < len(self.data)):
            raise IndexError("Index has to be 0 <= index < len(data).")
        if index == 0:
            return None
        current = self.data[index]
        previous = self.data[index - 1]
        return round(current.measure - previous.measure, 1)

    def get_log_with_dif(self) -> WatchLogFrame:
        table = []
        for i, entry in enumerate(self.data):
            table.append(Record(**entry, difference=self.difference(i)))
        return self.__class__(table)

    def fill(self, interpolation_method: type[InterpolationAbstract]) -> WatchLogFrame:
        SECONDS_IN_DAY = 24 * 60 * 60

        data = [(record.time_as_float, record.measure) for record in self.data]
        if len(self.data) == 0:
            return self.__class__([])

        f = interpolation_method.calculate(data)
        start = int(self.data[0].time_as_float)
        end = int(self.data[-1].time_as_float)

        table = []
        for time in range(start, end + 1, SECONDS_IN_DAY):
            table.append(Record(datetime=time, measure=round(f(time), 1)))

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
