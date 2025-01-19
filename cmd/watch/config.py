from typing import Self
from pathlib import Path

from pydantic import BaseModel, ValidationError


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
    def _verify_write(cls, file: Path) -> bool:
        if not file.exists():
            return True
        try:
            cls.from_file(file)
            return True
        except ValidationError:
            return False

    @classmethod
    def from_file(cls, file: Path) -> Self:
        with open(file, 'r') as f:
            text = f.read()
        return cls.model_validate_json(text)

    def to_file(self, file: Path):
        if not self._verify_write(file):
            raise ValueError(f"Config file {str(file)} cannot be parsed. Fix or delete the file to continue.")
        with open(file, 'w') as f:
            f.write(self.model_dump_json(indent=4))
