from pydantic import BaseModel


class Auth(BaseModel):
    token: str
    expiration_minutes: int


class LoggedInUser(BaseModel):
    auth: Auth


class User(BaseModel):
    user_name: str
    password: str

