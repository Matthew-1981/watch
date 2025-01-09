from pydantic import BaseModel


class Auth(BaseModel):
    token: str


class LoggedInUser(BaseModel):
    auth: Auth


class User(BaseModel):
    user_name: str
    password: str

