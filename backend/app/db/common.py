from typing import TypeVar, Generic, Generator, Any


class DatabaseError(Exception):
    pass


T = TypeVar("T")


class Protected(Generic[T]):
    def __init__(self, value: T):
        self.value = value

    def __get__(self, instance: Any, owner: Any) -> T:
        return self.value

    def __set__(self, instance: Any, value: T):
        raise AttributeError("Protected fields cannot be modified")

    def __repr__(self) -> str:
        return repr(self.value)

    @classmethod
    def __get_validators__(cls) -> Generator:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any, field: Any) -> "Protected":
        if not isinstance(value, cls):
            value = cls(value)
        return value
