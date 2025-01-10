import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from fastapi import HTTPException, status
from mysql.connector.aio.cursor import MySQLCursor

from .db import UserRecord, TokenRecord, NewToken, DBAccess, OperationError
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
    if new_expiration > token.data.expiration:
        token.data.expiration = new_expiration
    await token.update(cursor)
    return token


class GetUserCreator:

    def __init__(self, db_access: DBAccess):
        self.access = db_access

    async def get_user(self, request: LoggedInUser) -> UserRecord:
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
        return user

    async def __call__(self, request: LoggedInUser) -> UserRecord:
        return await self.get_user(request)
