import secrets
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine

from passlib.context import CryptContext
from mysql.connector.aio.cursor import MySQLCursor

from .db import UserRecord, TokenRecord, NewToken, DBAccess
from .messages import LoggedInUser

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
    token.data.expiration = new_expiration
    await token.update(cursor)
    return token


def create_get_user_function(db_access: DBAccess) -> Callable[[LoggedInUser], Coroutine[Any, Any, UserRecord]]:

    async def get_user(request: LoggedInUser) -> UserRecord:
        async with db_access.access() as wp:
            token = await TokenRecord.get_token_by_value(wp.cursor, request.auth.token)
            if token.data.expiration < datetime.now():
                raise ValueError
            await update_token(wp.cursor, token, expiration_minutes=30)
            user = await UserRecord.get_user_by_id(wp.cursor, token.data.user_id)
        return user

    return get_user
