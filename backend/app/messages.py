from pydantic import BaseModel


class BaseMessage(BaseModel):
    pass


class AuthMessage(BaseMessage):
    token: str
    expiration_minutes: int


class LoggedInUserMessage(BaseMessage):
    auth: AuthMessage


class UserRegisterMessage(BaseMessage):
    user_name: str
    password: str


class UserLoginMessage(UserRegisterMessage):
    expiration_minutes: int


class EditWatchMessage(LoggedInUserMessage):
    name: str


class SpecifyWatchDataMessage(LoggedInUserMessage):
    watch_name: str
    cycle: int
