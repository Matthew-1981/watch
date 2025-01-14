from typing import Self
from pathlib import Path

from pydantic import BaseModel


class ConfigUser(BaseModel):
    username: str
    password: str


class ConfigServer(BaseModel):
    host: str
    token_expiration_minutes: int = 30


class ConfigContents(BaseModel):
    config_server: ConfigServer
    config_user: ConfigUser
    default_watch: str | None

    @classmethod
    def from_file(cls, file: Path) -> Self:
        with open(file) as f:
            text = f.read()
        return cls.model_validate_json(text)

    def to_file(self, file: Path):
        with open(file) as f:
            f.write(self.model_dump_json(indent=4))
