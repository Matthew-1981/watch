from datetime import datetime
from typing import Self

from pydantic import BaseModel
from mysql.connector.aio.cursor import MySQLCursor

from .common import DatabaseError, Protected


class NewUser(BaseModel):
    user_name: str
    password_hash: str
    date_of_creation: datetime


class ExistingUser(NewUser):
    user_id: Protected[int]


class UserRecord:

    def __init__(self, row: ExistingUser):
        self.data = row

    async def update(self, cursor: MySQLCursor):
        await cursor.execute(
            "UPDATE users SET user_name = %s, password_hash = %s, date_of_creation = %s WHERE user_id = %s",
            (self.data.user_name, self.data.password_hash, self.data.date_of_creation, self.data.user_id)
        )
        if cursor.rowcount != 1:
            raise DatabaseError()

    @classmethod
    async def get_user_by_id(cls, cursor: MySQLCursor, user_id: int) -> Self:
        await cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        row = await cursor.fetchone()
        if row is None:
            raise DatabaseError()
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
            raise DatabaseError()
        user = ExistingUser(
            user_id=row[0],
            user_name=row[1],
            password_hash=row[2],
            date_of_creation=row[3]
        )
        return cls(user)

    @classmethod
    async def new_user(cls, cursor: MySQLCursor, user: NewUser) -> Self:
        await cursor.execute(
            "INSERT INTO users (user_name, password_hash, date_of_creation) VALUES (%s, %s, %s)",
            (user.user_name, user.password_hash, user.date_of_creation)
        )
        if cursor.rowcount != 1:
            raise DatabaseError
        return await cls.get_user_by_name(cursor, user.user_name)
