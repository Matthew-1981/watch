from typing import Self
from datetime import datetime

from .security import AuthBundle
from pydantic import BaseModel


class BaseResponse(BaseModel):
    pass


class AuthResponse(BaseResponse):
    user: str
    expiration_date: datetime

    @classmethod
    def parse(cls, auth_bundle: AuthBundle) -> Self:
        return cls(
            user=auth_bundle.user.data.user_name,
            expiration_date=auth_bundle.token.data.expiration
        )


class LoggedInResponse(BaseResponse):
    auth: AuthResponse


class TokenResponse(BaseResponse):
    token: str
    expiration_date: datetime


class UserCreationResponse(BaseResponse):
    user_name: str
    creation_date: datetime


class WatchElementResponse(BaseResponse):
    name: str
    date_of_creation: datetime
    cycles: list[int]


class WatchListResponse(LoggedInResponse):
    watches: list[WatchElementResponse]


class WatchEditResponse(LoggedInResponse):
    name: str
    date_of_creation: datetime
