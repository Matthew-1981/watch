import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from fastapi import HTTPException, status
from mysql.connector.aio.cursor import MySQLCursor
from pydantic import BaseModel

from .db import UserRecord, TokenRecord, NewToken, DBAccess, OperationError, NewUser, ConstraintError
from . import messages

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def create_token(cursor: MySQLCursor, user_id: int, expiration_minutes: int) -> TokenRecord:
    new_token = NewToken(
        user_id=user_id,
        token=secrets.token_urlsafe(32),
        expiration=datetime.now() + timedelta(minutes=expiration_minutes)
    )
    token = await TokenRecord.new_token(cursor, new_token)
    return token


async def update_token(cursor: MySQLCursor, token: TokenRecord, expiration_minutes: int) -> TokenRecord:
    new_expiration = datetime.now() + timedelta(minutes=expiration_minutes)
    if new_expiration > token.data.expiration:
        token.data.expiration = new_expiration
    await token.update(cursor)
    return token


class CreateUserCreator:

    def __init__(self, db_access: DBAccess):
        self.access = db_access

    async def create_user(self, request: messages.UserRegisterMessage) -> UserRecord:
        new_user = NewUser(
            user_name=request.user_name,
            password_hash=hash_password(request.password),
            date_of_creation=datetime.now()
        )
        async with self.access.access() as wp:
            try:
                user = await UserRecord.new_user(wp.cursor, new_user)
            except ConstraintError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"User {request.user_name} already exists.")
            await wp.commit()
        return user

    async def __call__(self, request: messages.UserRegisterMessage) -> UserRecord:
        return await self.create_user(request)



class LoginUserCreator:

    def __init__(self, db_access: DBAccess):
        self.access = db_access

    async def login_user(self, request: messages.UserLoginMessage) -> tuple[UserRecord, TokenRecord]:
        async with self.access.access() as wp:
            try:
                user = await UserRecord.get_user_by_name(wp.cursor, request.user_name)
            except OperationError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"No user with name '{request.user_name}'.")
            if not verify_password(request.password, user.data.password_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail=f"Wrong password for user {request.user_name}.")
            token = await create_token(wp.cursor, user.data.user_id, request.expiration_minutes)
            await wp.commit()
        return user, token

    async def __call__(self, request: messages.UserLoginMessage) -> tuple[UserRecord, TokenRecord]:
        return await self.login_user(request)


class AuthBundle(BaseModel):
    user: UserRecord
    token: TokenRecord

    class Config:
        arbitrary_types_allowed = True


class GetUserCreator:

    def __init__(self, db_access: DBAccess):
        self.access = db_access

    async def get_user(self, request: messages.LoggedInUserMessage) -> AuthBundle:
        async with self.access.access() as wp:
            try:
                token = await TokenRecord.get_token_by_value(wp.cursor, request.auth.token)
            except OperationError:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid or expired.")
            if token.data.expiration < datetime.now():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token.")
            await update_token(wp.cursor, token, request.auth.expiration_minutes)
            user = await UserRecord.get_user_by_id(wp.cursor, token.data.user_id)
            await wp.commit()
        return AuthBundle(user=user, token=token)

    async def __call__(self, request: messages.LoggedInUserMessage) -> AuthBundle:
        return await self.get_user(request)


class SecurityCreator:

    def __init__(self, db_access: DBAccess):
        self.get_user = GetUserCreator(db_access)
        self.login_user = LoginUserCreator(db_access)
        self.register_user = CreateUserCreator(db_access)
