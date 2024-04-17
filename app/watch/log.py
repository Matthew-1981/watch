from __future__ import annotations
from typing import Any, Self

import datetime as dt
from math import sqrt

from app.watch.interpolation.base import InterpolationAbstract


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

        f = interpolation_method.calculate(data)
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
