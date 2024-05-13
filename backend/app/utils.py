from typing import Any


def convert_table(headers: tuple[str], table: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    return [{header: value for header, value in zip(headers, row)} for row in table]
