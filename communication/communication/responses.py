from datetime import datetime

from pydantic import BaseModel


class BaseResponse(BaseModel):
    pass


class AuthResponse(BaseResponse):
    user: str
    expiration_date: datetime


class LoggedInResponse(BaseResponse):
    auth: AuthResponse


class LogOutResponse(BaseResponse):
    user: str
    token: str


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


class LogResponse(BaseResponse):
    log_id: int | None
    time: datetime
    measure: float
    difference: float | None


class LogListResponse(LoggedInResponse):
    logs: list[LogResponse]


class StatsResponse(LoggedInResponse):
    average: float | None
    deviation: float | None
    delta: float | None

class LogAddedResponse(LoggedInResponse):
    log_id: int
    time: datetime
    measure: float
