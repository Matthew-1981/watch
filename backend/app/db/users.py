from datetime import datetime
from typing import Self

from pydantic import BaseModel
from mysql.connector.aio.cursor import MySQLCursor
from mysql.connector import Error

from .exceptions import OperationError, ConstraintError


class NewUser(BaseModel):
    user_name: str
    password_hash: str
    date_of_creation: datetime


class ExistingUser(NewUser):
    user_id: int


class UserRecord:

    def __init__(self, row: ExistingUser):
        self._initial_user_id = row.user_id
        self.data = row

    def check_integrity(self) -> bool:
        return self.data.user_id == self._initial_user_id

    async def update(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "UPDATE users SET user_name = %s, password_hash = %s, date_of_creation = %s WHERE user_id = %s",
                (self.data.user_name, self.data.password_hash, self.data.date_of_creation, self.data.user_id)
            )
        except Error as e:
            raise ConstraintError from e
        # if cursor.rowcount != 1:
        #     raise OperationError()

    async def delete(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "DELETE FROM users WHERE user_id = %s",
                (self.data.user_id,)
            )
        except Error as e:
            raise ConstraintError from e
        if cursor.rowcount != 1:
            raise OperationError()

    @classmethod
    async def get_user_by_id(cls, cursor: MySQLCursor, user_id: int) -> Self:
        await cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        user = ExistingUser(
            user_id=row[0],
            user_name=row[1],
            password_hash=row[2],
            date_of_creation=row[3]
        )
        return cls(user)

    @classmethod
    async def get_user_by_name(cls, cursor: MySQLCursor, user_name: str) -> Self:
        await cursor.execute("SELECT * FROM users WHERE user_name = %s", (user_name,))
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        user = ExistingUser(
            user_id=row[0],
            user_name=row[1],
            password_hash=row[2],
            date_of_creation=row[3]
        )
        return cls(user)

    @classmethod
    async def new_user(cls, cursor: MySQLCursor, user: NewUser) -> Self:
        try:
            await cursor.execute(
                "INSERT INTO users (user_name, password_hash, date_of_creation) VALUES (%s, %s, %s)",
                (user.user_name, user.password_hash, user.date_of_creation)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()
        return await cls.get_user_by_name(cursor, user.user_name)


class NewToken(BaseModel):
    user_id: int
    token: str
    expiration: datetime


class ExistingToken(NewToken):
    token_id: int


class TokenRecord:

    def __init__(self, row: ExistingToken):
        self._initial_ids = (row.user_id, row.token_id)
        self.data = row

    def check_integrity(self) -> bool:
        return self._initial_ids == (self.data.user_id, self.data.token_id)

    async def update(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "UPDATE session_token SET user_id = %s, token = %s, expiration = %s WHERE token_id = %s",
                (self.data.user_id, self.data.token,  self.data.expiration, self.data.token_id)
            )
        except Error as e:
            raise ConstraintError() from e
        # if cursor.rowcount != 1:
        #     raise OperationError()

    async def delete(self, cursor: MySQLCursor):
        if not self.check_integrity():
            raise RuntimeError
        try:
            await cursor.execute(
                "DELETE FROM session_token WHERE token_id = %s",
                (self.data.token_id,)
            )
        except Error as e:
            raise ConstraintError from e
        if cursor.rowcount != 1:
            raise OperationError()

    @classmethod
    async def get_token_by_id(cls, cursor: MySQLCursor, token_id: int) -> Self:
        await cursor.execute("SELECT * FROM session_token WHERE token_id = %s", (token_id,))
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        token = ExistingToken(
            token_id=row[0],
            user_id=row[1],
            token=row[2],
            expiration=row[3]
        )
        return cls(token)

    @classmethod
    async def get_token_by_value(cls, cursor: MySQLCursor, token: str) -> Self:
        await cursor.execute("SELECT * FROM session_token WHERE token = %s", (token,))
        row = await cursor.fetchone()
        if row is None:
            raise OperationError()
        token = ExistingToken(
            token_id=row[0],
            user_id=row[1],
            token=row[2],
            expiration=row[3]
        )
        return cls(token)

    @classmethod
    async def new_token(cls, cursor: MySQLCursor, token: NewToken) -> Self:
        try:
            await cursor.execute(
                "INSERT INTO session_token (user_id, token, expiration) VALUES (%s, %s, %s)",
                (token.user_id, token.token, token.expiration)
            )
        except Error as e:
            raise ConstraintError() from e
        if cursor.rowcount != 1:
            raise OperationError()
        return await cls.get_token_by_value(cursor, token.token)
