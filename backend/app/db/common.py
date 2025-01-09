from typing import TypeVar, Generic, Generator, Any


class DatabaseError(Exception):
    pass


T = TypeVar("T")
