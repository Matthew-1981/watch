from abc import ABC, abstractmethod
from typing import Self


class InterpolationAbstract(ABC):

    @classmethod
    @abstractmethod
    def calculate(cls, data: list[tuple[float, float]]) -> Self:
        ...

    @abstractmethod
    def __call__(self, x: float) -> float:
        ...
