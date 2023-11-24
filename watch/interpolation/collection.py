from __future__ import annotations
from typing import Self, Optional

from .base import InterpolationAbstract


class QubicSplineInterpolation(InterpolationAbstract):

    def __init__(self):
        self.t: list[float] = []
        self.y: list[float] = []
        self.z: list[float] = []
        self.h: list[float] = []
        self.n: int = 0

    @classmethod
    def calculate(cls, data: list[tuple[float, float]]) -> Self:
        out = cls()
        size = len(data)
        out.n = size - 1

        out.t = [i for i, _ in data]
        out.y = [j for _, j in data]
        out.z = [0] * size
        out.h = [0] * size

        b = [0] * size
        u = [0] * size
        v = [0] * size

        for i in range(0, out.n):
            out.h[i] = out.t[i + 1] - out.t[i]
            b[i] = 6 * (out.y[i + 1] - out.y[i]) / out.h[i]
        u[1] = 2 * (out.h[0] + out.h[1])
        v[1] = b[1] - b[0]
        for i in range(2, out.n):
            u[i] = 2 * (out.h[i - 1] + out.h[i]) - pow(out.h[i - 1], 2) / u[i - 1]
            v[i] = b[i] - b[i - 1] - out.h[i - 1] * v[i - 1] / u[i - 1]
        out.z[out.n] = 0
        for i in range(out.n - 1, 0, -1):
            out.z[i] = (v[i] - out.h[i] * out.z[i + 1]) / u[i]
        out.z[0] = 0

        return out

    def __call__(self, x: float) -> float:
        i = self.n
        while i >= 1 and x - self.t[i] < 0:
            i -= 1

        ai = (1 / (6 * self.h[i])) * (self.z[i + 1] - self.z[i])
        bi = self.z[i] / 2
        ci = (-self.h[i] / 6) * (self.z[i + 1] + 2 * self.z[i]) + (1 / self.h[i]) * (self.y[i + 1] - self.y[i])
        return self.y[i] + (x - self.t[i]) * (ci + (x - self.t[i]) * (bi + (x - self.t[i]) * ai))


class LinearInterpolation(InterpolationAbstract):

    def __init__(self, data: list[tuple[float, float]]):
        self.x = [i for i, _ in data]
        self.y = [j for _, j in data]
        self.lines: Optional[list[tuple[float, float]]] = None
        self.n: Optional[int] = None

    @classmethod
    def calculate(cls, data: list[tuple[float, float]]) -> Self:
        out = cls(data)
        lines: list[tuple[float, float]] = [(0.0, out.y[0])]

        for p1, p2 in zip(data[:-1], data[1:]):
            x1, y1 = p1
            x2, y2 = p2
            a = (y2 - y1) / (x2 - x1)
            b = y1 - a * x1
            lines.append((a, b))

        lines.append((0.0, out.y[-1]))

        out.lines = lines
        out.n = len(data) - 1

        return out

    def __call__(self, x: float) -> float:
        i = self.n
        while i >= 0 and x < self.x[i]:
            i -= 1

        a, b = self.lines[i + 1]
        return a * x + b
