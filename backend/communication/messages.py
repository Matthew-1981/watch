from datetime import datetime

from pydantic import BaseModel, Field


class BaseMessage(BaseModel):
    pass


class AuthMessage(BaseMessage):
    token: str
    expiration_minutes: int = Field(..., gt=5)


class LoggedInUserMessage(BaseMessage):
    auth: AuthMessage


class UserRegisterMessage(BaseMessage):
    user_name: str = Field(..., pattern=r'^[a-zA-Z0-9_]{4,32}$')
    password: str = Field(..., pattern=r'^[A-Za-z0-9@$!%*?&_-]{8,64}$')


class UserLoginMessage(UserRegisterMessage):
    expiration_minutes: int = Field(..., gt=5)


class EditWatchMessage(LoggedInUserMessage):
    name: str = Field(..., pattern=r'^[a-zA-Z0-9_ -]{4,32}$')


class SpecifyWatchDataMessage(LoggedInUserMessage):
    watch_name: str = Field(..., pattern=r'^[a-zA-Z0-9_ -]{4,32}$')
    cycle: int = Field(..., gt=-1)


class SpecifyLogDataMessage(SpecifyWatchDataMessage):
    log_id: int = Field(..., gt=-1)


class CreateMeasurementMessage(SpecifyWatchDataMessage):
    datetime: datetime
    measure: float
