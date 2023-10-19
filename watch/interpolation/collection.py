from .base import InterpolationAbstract
from typing import Self


class QubicSplineInterpolation(InterpolationAbstract):

    def __init__(self, data: list[tuple[float, float]]):
        self.data = data
        self.t: list[float] = []
        self.y: list[float] = []
        self.z: list[float] = []
        self.h: list[float] = []
        self.n: int = 0

    def calculate(self) -> Self:
        if len(self.data) == 0:
            raise Exception

        size = len(self.data)
        self.n = size - 1

        self.t = [i for i, _ in self.data]
        self.y = [j for _, j in self.data]
        self.z = [0] * size
        self.h = [0] * size

        b = [0] * size
        u = [0] * size
        v = [0] * size

        for i in range(0, self.n):
            self.h[i] = self.t[i + 1] - self.t[i]
            b[i] = 6 * (self.y[i + 1] - self.y[i]) / self.h[i]
        u[1] = 2 * (self.h[0] + self.h[1])
        v[1] = b[1] - b[0]
        for i in range(2, self.n):
            u[i] = 2 * (self.h[i - 1] + self.h[i]) - pow(self.h[i - 1], 2) / u[i - 1]
            v[i] = b[i] - b[i - 1] - self.h[i - 1] * v[i - 1] / u[i - 1]
        self.z[self.n] = 0
        for i in range(self.n - 1, 0, -1):
            self.z[i] = (v[i] - self.h[i] * self.z[i + 1]) / u[i]
        self.z[0] = 0

        return self

    def __call__(self, x: float) -> float:
        i = self.n
        while i >= 1 and x - self.t[i] < 0:
            i -= 1

        ai = (1 / (6 * self.h[i])) * (self.z[i + 1] - self.z[i])
        bi = self.z[i] / 2
        ci = (-self.h[i] / 6) * (self.z[i + 1] + 2 * self.z[i]) + (1 / self.h[i]) * (self.y[i + 1] - self.y[i])
        return self.y[i] + (x - self.t[i]) * (ci + (x - self.t[i]) * (bi + (x - self.t[i]) * ai))
