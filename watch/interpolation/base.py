from abc import ABC, abstractmethod
from typing import Self


class InterpolationAbstract(ABC):

    @abstractmethod
    def __init__(self, data: list[tuple[float, float]]):
        self.data = data

    @abstractmethod
    def calculate(self) -> Self:
        ...

    @abstractmethod
    def __call__(self, x: float) -> float:
        ...
